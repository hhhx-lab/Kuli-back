import json
import re

from sqlalchemy.orm import Session

from app.models.entities import AgentMessage, AgentSession, KnowledgeArticle, Order, User
from app.services.llm import complete_chat
from app.services.rag import KnowledgeHit, search_knowledge_hits


XIAOKU_SYSTEM_PROMPT = (
    "你是酷里的 3D 小猫服务助手小酷。目标是帮助用户理解酷里服务、整理需求、查看自己的订单进度。"
    "只回答酷里业务、服务目录、文档中心、订单状态、材料准备、付款验收和安全边界相关问题。"
    "不要回答无关闲聊、破解绕过、违法违规、内部字段、其他用户订单。"
    "不要承诺固定价格、周期、账号开通成功率或第三方平台结果。"
    "如果知识不足，说明现在没有足够资料，并引导用户写小纸条或联系管理员。"
    "回答保持自然、短、有下一步。"
)

SENSITIVE_TERMS = ["破解", "盗号", "绕过", "验证码", "密码", "私钥", "支付凭证", "身份证"]
UNRELATED_TERMS = ["天气", "股票", "彩票", "写诗", "历史", "八卦", "游戏攻略"]
INTERNAL_TERMS = ["成本", "利润", "内部备注", "后台私密", "其他用户", "demo 用户订单"]
SERVICE_KEYWORDS = [
    ("document-processing", ["ppt", "pdf", "word", "excel", "文档", "翻译", "排版", "表格"]),
    ("tool-development", ["网页", "网站", "小工具", "脚本", "demo", "小程序", "自动化"]),
    ("deployment-config", ["部署", "服务器", "域名", "证书", "数据库", "上线"]),
    ("api-token", ["api", "token", "key", "sdk", "中转"]),
    ("ai-tools", ["gpt", "claude", "ai 工具", "账号", "订阅"]),
]


def create_session(db: Session, user: User | None, visitor_id: str | None, page_path: str) -> AgentSession:
    session = AgentSession(user_id=user.id if user else None, visitor_id=visitor_id, page_path=page_path)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def chat(db: Session, session: AgentSession, message: str, user: User | None) -> dict[str, object]:
    db.add(AgentMessage(session_id=session.id, role="user", content=message))
    answer = answer_message(db, message, user)
    db.add(AgentMessage(session_id=session.id, role="assistant", content=answer["answer"], actions_json=json.dumps(answer["actions"], ensure_ascii=False)))
    db.commit()
    return answer


def answer_message(db: Session, message: str, user: User | None) -> dict[str, object]:
    if _has_any(message, SENSITIVE_TERMS):
        citations = _citations_for_query(db, "哪些信息不要发 密码 验证码 敏感信息", fallback=[{"title": "常见问题", "to": "/help/faq#sensitive-info", "source": "doc:faq"}])
        return {
            "answer": "这个不能帮你处理。密码、验证码、私钥、支付凭证这类敏感信息不要发给我；如果确实涉及账号类操作，后续由管理员确认安全方式。",
            "actions": [{"label": "查看安全说明", "to": "/help/faq#sensitive-info"}, {"label": "写小纸条", "to": "/note"}],
            "citations": citations,
            "draft": None,
        }

    if _has_any(message, INTERNAL_TERMS):
        return {
            "answer": "这类内容属于酷里内部管理信息或其他用户范围，小酷不能查看或展示。你可以问我自己的订单进度、需要补什么材料，或者查看订单页。",
            "actions": [{"label": "查看我的订单", "to": "/orders"}, {"label": "查看订单规则", "to": "/help/concepts#order-status"}],
            "citations": _citations_for_query(db, "小酷 权限 订单 状态", fallback=[{"title": "核心概念", "to": "/help/concepts#order-status", "source": "doc:concepts"}]),
            "draft": None,
        }

    if _has_any(message, UNRELATED_TERMS):
        return {
            "answer": "这个超出酷里业务知识范围啦。我可以帮你了解服务、准备材料、整理小纸条、解释订单状态和付款验收边界。",
            "actions": [{"label": "查看服务", "to": "/services"}, {"label": "看快速开始", "to": "/help/quick-start"}],
            "citations": _citations_for_query(db, "快速开始 酷里 服务", fallback=[{"title": "快速开始", "to": "/help/quick-start", "source": "doc:quick-start"}]),
            "draft": None,
        }

    if "订单" in message and user:
        order = db.query(Order).filter(Order.owner_user_id == user.id).order_by(Order.updated_at.desc()).first()
        if order:
            return {
                "answer": f"小酷看了一下，你最近的订单是 {order.order_number}，当前状态是「{order.status}」。下一步：{order.next_action}。",
                "actions": [{"label": "查看我的订单", "to": "/orders"}],
                "citations": [{"title": "我的订单", "to": f"/orders/{order.order_number}", "source": "user-order"}],
                "draft": None,
            }
    if "收费" in message or "价格" in message or "钱" in message:
        text = "可以先免费判断能不能做。具体报价需要看材料、范围、周期和风险，小酷不会替管理员直接承诺价格。"
        hits = search_knowledge_hits(db, "收费 价格 定金 报价", limit=5)
    elif "材料" in message or "上传" in message:
        text = "你可以先准备截图、源文件、目标效果、截止时间和预算区间。说不清也没关系，先写小纸条。"
        hits = search_knowledge_hits(db, "材料 上传 截图 源文件", limit=5)
    else:
        hits = search_knowledge_hits(db, message, limit=5)
        articles = [hit.article for hit in hits]
        text = answer_from_knowledge(message, articles, hits)
    return {
        "answer": text,
        "actions": _actions_for_message(message),
        "citations": _citations_from_hits(hits),
        "draft": _draft_from_message(message),
    }


def answer_from_knowledge(message: str, articles: list[KnowledgeArticle], hits: list[KnowledgeHit]) -> str:
    context = "\n\n".join(f"【{hit.article.title} / {hit.chunk.section}】\n{hit.chunk.content}" for hit in hits[:5])
    remote = complete_chat(
        system=XIAOKU_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"知识库：\n{context or '暂无匹配知识'}\n\n用户问题：{message}"},
        ],
    )
    if remote:
        return remote
    if articles:
        first = articles[0]
        summary = _compact_body(first.body)
        return f"小酷按知识库看，{summary} 你可以先把已有材料和想要的结果写成小纸条，我会帮你继续拆。"
    return "我是小酷。你可以直接说卡在哪里，我会帮你判断属于哪类服务，并引导你写小纸条。"


def _has_any(message: str, terms: list[str]) -> bool:
    lowered = message.lower()
    return any(term.lower() in lowered for term in terms)


def _compact_body(body: str) -> str:
    plain = re.sub(r"[#>*_`{}\[\]]+", " ", body)
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain[:180] + ("..." if len(plain) > 180 else "")


def _actions_for_message(message: str) -> list[dict[str, str]]:
    draft = _draft_from_message(message)
    actions = [{"label": "帮我写小纸条", "to": "/note"}, {"label": "查看服务", "to": "/services"}]
    if draft:
        actions[0] = {"label": "用这版写小纸条", "to": f"/note?service={draft['serviceSlug']}"}
        actions.append({"label": "查看相关服务", "to": f"/services/{draft['serviceSlug']}"})
    if "开始" in message or "怎么" in message:
        actions.append({"label": "看快速开始", "to": "/help/quick-start"})
    return actions[:4]


def _draft_from_message(message: str) -> dict[str, object] | None:
    service_slug = _detect_service_slug(message)
    if not service_slug and not _looks_like_service_need(message):
        return None
    service_slug = service_slug or "not-sure"
    missing = []
    if not re.search(r"截止|时间|今天|明天|周|号|日期", message):
        missing.append("截止时间")
    if not re.search(r"文件|截图|链接|参考|材料|word|pdf|ppt|excel", message, re.IGNORECASE):
        missing.append("参考材料")
    if not re.search(r"预算|价格|钱|报价", message):
        missing.append("预算区间")
    return {
        "serviceSlug": service_slug,
        "summary": f"用户想咨询：{message.strip()[:90]}",
        "missingFields": missing[:4],
    }


def _detect_service_slug(message: str) -> str | None:
    lowered = message.lower()
    for slug, keywords in SERVICE_KEYWORDS:
        if any(keyword.lower() in lowered for keyword in keywords):
            return slug
    return None


def _looks_like_service_need(message: str) -> bool:
    return bool(re.search(r"想|需要|帮我|能不能做|可以做|做一个|整理|处理|配置", message))


def _citations_for_query(db: Session, query: str, *, fallback: list[dict[str, str]]) -> list[dict[str, str]]:
    citations = _citations_from_hits(search_knowledge_hits(db, query, limit=5))
    return citations or fallback


def _citations_from_hits(hits: list[KnowledgeHit]) -> list[dict[str, str]]:
    citations: list[dict[str, str]] = []
    seen: set[str] = set()
    for hit in hits:
        citation = _citation_from_hit(hit)
        if citation["to"] in seen:
            continue
        citations.append(citation)
        seen.add(citation["to"])
        if len(citations) >= 5:
            break
    return citations


def _citation_from_hit(hit: KnowledgeHit) -> dict[str, str]:
    source = hit.article.source
    if source.startswith("doc:"):
        anchor = f"#{hit.chunk.anchor}" if hit.chunk.anchor else ""
        return {"title": hit.article.title, "to": f"/help/{hit.chunk.slug}{anchor}", "source": source}
    if source.startswith("service:"):
        slug = source.split(":", 1)[1]
        return {"title": hit.article.title, "to": f"/services/{slug}", "source": source}
    if source == "rule:required-materials":
        return {"title": "指南", "to": "/help/guides#upload-materials", "source": source}
    if source == "rule:payment-boundary":
        return {"title": "常见问题", "to": "/help/faq#deposit", "source": source}
    if source == "rule:order-status":
        return {"title": "核心概念", "to": "/help/concepts#order-status", "source": source}
    if source.startswith("safety:"):
        return {"title": "常见问题", "to": "/help/faq#sensitive-info", "source": source}
    return {"title": hit.article.title, "to": "/help/quick-start", "source": source}

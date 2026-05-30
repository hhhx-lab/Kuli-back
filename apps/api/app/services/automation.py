import json
import re
from sqlalchemy.orm import Session

from app.models.entities import Order, OrderAISummary, OrderAutomationSuggestion, OrderTodo, now_iso


def infer_intent(text: str) -> str:
    if re.search(r"先问|先看看|能不能|咨询|不知道|不确定|先报价", text, re.I):
        return "consultation"
    if re.search(r"报价|多少钱|预算|价格", text, re.I):
        return "quote_request"
    return "ready_to_start"


def missing_fields_for(text: str) -> list[str]:
    missing: list[str] = []
    if not re.search(r"今天|明天|后天|周|天|小时|截止|ddl|deadline|\d", text, re.I):
        missing.append("补充截止时间")
    if not re.search(r"文件|截图|图片|pdf|word|excel|ppt|代码|链接", text, re.I):
        missing.append("上传源文件、截图或示例")
    if not re.search(r"预算|钱|价格|报价|\d+元", text, re.I):
        missing.append("说明预算区间或是否先报价")
    return missing


def service_confidence(service_slug: str | None, text: str) -> float:
    if not service_slug or service_slug == "not-sure":
        return 0.45
    keyword_map = {
        "ai-tools": ["gpt", "claude", "gemini", "账号", "api", "token", "key"],
        "document-processing": ["pdf", "word", "ppt", "excel", "翻译", "排版", "ocr"],
        "tool-development": ["网页", "demo", "脚本", "小程序", "自动化", "后台"],
        "deployment-config": ["部署", "服务器", "域名", "证书", "环境变量"],
        "api-token": ["api", "token", "key", "sdk", "模型"],
    }
    words = keyword_map.get(service_slug, [])
    return 0.82 if any(word.lower() in text.lower() for word in words) else 0.62


def polish_demand(demand: str, service_title: str | None = None, service_slug: str | None = None) -> dict[str, object]:
    clean = " ".join(demand.split())
    missing = missing_fields_for(clean)
    intro = f"这件事大概属于「{service_title}」。" if service_title else "我还不确定它属于哪一类。"
    return {
        "polishedDemand": f"{intro}我想先判断能不能帮我处理：{clean}。如果可以，请告诉我需要补充哪些材料、预计周期和报价方式。",
        "hints": missing or ["描述已经比较清楚，可以继续提交给酷里判断"],
        "intent": infer_intent(clean),
        "missingFields": missing,
        "serviceConfidence": service_confidence(service_slug, clean),
    }


def ensure_automation_for_order(db: Session, order: Order, reason: str = "order_changed") -> None:
    text = f"{order.original_demand} {order.demand} {order.budget} {order.category}"
    missing = missing_fields_for(text)
    next_action = "确认需求范围和材料是否齐全"
    suggested_status = "clarifying" if order.intent == "consultation" or missing else "quoted"
    if order.status == "quoted":
        next_action = "等待客户确认报价和付款方式"
        suggested_status = "deposit_pending"
    elif order.status == "review":
        next_action = "等待客户验收交付物"
        suggested_status = "completed"
    elif order.status == "final_payment_pending":
        next_action = "确认尾款到账后完成订单"
        suggested_status = "completed"
    elif order.status == "completed":
        next_action = "归档订单并沉淀可复用案例"
        suggested_status = None
    elif order.status == "cancelled":
        next_action = "订单已取消，无需继续推进"
        suggested_status = None
    elif missing:
        next_action = "追问：" + "、".join(missing)

    order.next_action = next_action
    order.ai_status = f"自动化建议：{next_action}"
    order.last_automation_run_at = now_iso()

    db.add(
        OrderAutomationSuggestion(
            order_number=order.order_number,
            kind="next_action",
            severity="requires_approval" if suggested_status in {"quoted", "completed", "cancelled"} else "suggestion",
            summary=next_action,
            suggested_status=suggested_status,
            suggested_message=build_reply_draft(order, missing),
            confidence=0.72,
            reason=reason,
            source_refs=json.dumps(["order", "service_catalog"], ensure_ascii=False),
        )
    )
    db.add(OrderTodo(order_number=order.order_number, title=next_action, source="automation"))
    db.add(
        OrderAISummary(
            order_number=order.order_number,
            summary=f"用户需求方向是「{order.category}」，当前意图是 {order.intent}，下一步建议：{next_action}。",
            risk_flags=json.dumps(["不得承诺固定价格或周期"], ensure_ascii=False),
            suggested_questions=json.dumps(missing, ensure_ascii=False),
        )
    )
    db.commit()


def build_reply_draft(order: Order, missing: list[str]) -> str:
    if missing:
        return f"收到，我先帮你判断一下。为了更准确报价和确认能不能做，麻烦补充：{'、'.join(missing)}。"
    return "收到，你的描述已经比较清楚了。酷里会先确认范围、风险和预计周期，再给你下一步报价或处理建议。"

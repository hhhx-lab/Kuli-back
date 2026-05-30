import json


def _service(
    slug: str,
    title: str,
    tag: str,
    summary: str,
    audience: list[str],
    common_needs: list[str],
    deliverables: list[str],
    required_materials: list[str],
    risks: list[str],
) -> dict[str, str]:
    details = {
        "slug": slug,
        "title": title,
        "tag": tag,
        "summary": summary,
        "audience": audience,
        "commonNeeds": common_needs,
        "deliverables": deliverables,
        "requiredMaterials": required_materials,
        "priceRange": "先免费判断，确认可做后报价",
        "timeline": "小问题当天，复杂需求按阶段估",
        "risks": risks,
        "cases": [{"title": common_needs[0], "description": f"酷里会先判断「{common_needs[0]}」的材料、风险和交付边界。"}],
        "faq": [
            {"question": "可以先问问吗？", "answer": "可以。先写小纸条，酷里会先判断是否适合做，不会一上来就收费。"},
            {"question": "需要准备什么？", "answer": "最好提供截图、源文件、目标效果、截止时间和预算区间。"},
        ],
    }
    body = "\n".join(
        [
            f"{title}：{summary}",
            "适合人群：" + "、".join(audience),
            "常见需求：" + "、".join(common_needs),
            "交付物：" + "、".join(deliverables),
            "需要材料：" + "、".join(required_materials),
            f"价格/周期：{details['priceRange']}；{details['timeline']}",
            "风险边界：" + "、".join(risks),
            "FAQ：" + "；".join(f"{item['question']}：{item['answer']}" for item in details["faq"]),
        ]
    )
    return {
        "slug": slug,
        "title": title,
        "tag": tag,
        "summary": summary,
        "json": json.dumps(details, ensure_ascii=False),
        "knowledge_body": body,
        "tags": json.dumps([tag, slug], ensure_ascii=False),
    }


SERVICE_CATALOG = [
    _service(
        "ai-tools",
        "GPT / Claude / Google 相关",
        "AI 工具",
        "帮你理顺海外 AI 工具、账号、订阅、API 和 Claude Code 等使用路径。",
        ["想用 GPT / Claude 但卡在账号或支付的人", "需要 API Key / token / 中转配置的人"],
        ["账号注册与订阅路径判断", "API Key 获取与环境配置", "Claude Code 授权与模型接入", "模型选择和费用路径比较"],
        ["可执行配置步骤", "最小可运行示例", "风险与限制说明"],
        ["所在地区和付款方式", "报错截图", "目标平台或模型", "预算和用途"],
        ["第三方平台风控可能变化", "不承诺绕过平台审核", "不接盗号、破解、批量滥用"],
    ),
    _service(
        "document-processing",
        "文档与文件急救",
        "文档处理",
        "处理 PDF、Word、PPT、Excel、翻译、排版、格式转换、合并拆分和报错文件。",
        ["急着交材料但格式乱的人", "需要 PDF 翻译保留排版的人"],
        ["PDF 翻译保排版", "Word/PPT 格式修复", "Excel 表格清洗整理", "OCR/扫描件整理"],
        ["处理后的文档文件", "转换前后说明", "无法完全还原处的说明"],
        ["原始文件", "目标格式或语言", "截止时间", "样例或格式要求"],
        ["扫描件和复杂公式可能无法完美还原", "低质量源文件会影响效果"],
    ),
    _service(
        "tool-development",
        "小工具与网页 demo",
        "小工具开发",
        "把一句想法做成能看的网页、小程序原型、课程项目 demo 或自动化脚本。",
        ["需要课程项目或作品集 demo 的人", "想把重复工作自动化的人"],
        ["网页 demo", "课程项目页面", "自动化脚本", "简单后台和数据展示"],
        ["可运行源码或静态页面", "本地运行说明", "核心截图或演示链接"],
        ["核心功能", "参考图或草稿", "数据样例", "截止时间和交付格式"],
        ["第一版优先可演示", "部署上线和长期维护需另拆范围"],
    ),
    _service(
        "deployment-config",
        "部署与远程配置",
        "部署配置",
        "处理服务器、域名、数据库、环境变量、代理网络和远程排查。",
        ["上线前环境卡住的人", "本地能跑但线上挂掉的人"],
        ["服务器部署", "域名与证书", "数据库和环境变量", "构建失败排查"],
        ["部署结果或排查结论", "关键配置记录", "回滚/重启建议"],
        ["服务器或平台信息", "项目源码", "域名/数据库信息", "错误日志截图"],
        ["账号权限和费用由客户确认", "不默认长期托管", "敏感凭证需临时授权并及时更换"],
    ),
    _service(
        "api-token",
        "API Key / token",
        "API",
        "围绕 OpenAI、Claude、模型中转站、低价 token 和 SDK 调用做配置咨询。",
        ["有 key 但不会接入的人", "想比较模型渠道的人"],
        ["API Key 配置", "中转站接入", "SDK 最小示例", "调用报错排查"],
        ["可运行最小调用示例", "配置路径说明", "渠道风险提示"],
        ["目标模型或平台", "现有 key 或渠道", "报错日志", "预算和稳定性要求"],
        ["渠道稳定性不由酷里保证", "费用和合规由客户确认", "不接滥用平台的需求"],
    ),
    _service(
        "not-sure",
        "不知道怎么分",
        "先聊聊",
        "说不清也可以，直接截图、描述卡住的地方，酷里会帮你继续拆问题。",
        ["不知道需求属于哪类的人", "只有截图或一句想法的人"],
        ["需求判断", "范围拆解", "初步报价", "下一步建议"],
        ["问题归类", "可行路径", "材料清单", "是否进入正式订单的建议"],
        ["截图", "想达到的效果", "截止时间", "预算区间", "相关文件或报错"],
        ["描述越模糊越需要追问", "无法判断风险时不会直接开工", "违法违规需求不会接"],
    ),
]


def catalog_item(slug: str) -> dict[str, object] | None:
    for item in SERVICE_CATALOG:
        if item["slug"] == slug:
            return json.loads(item["json"])
    return None

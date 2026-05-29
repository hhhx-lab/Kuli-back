export type ServiceCatalogItem = {
  slug: string;
  title: string;
  tag: string;
  summary: string;
  audience: string[];
  commonNeeds: string[];
  deliverables: string[];
  requiredMaterials: string[];
  priceRange: string;
  timeline: string;
  risks: string[];
  cases: Array<{ title: string; description: string }>;
  faq: Array<{ question: string; answer: string }>;
};

export const serviceCatalog: ServiceCatalogItem[] = [
  {
    slug: "ai-tools",
    title: "GPT / Claude / Google 相关",
    tag: "AI 工具",
    summary: "帮你理顺海外 AI 工具、账号、订阅、API 和 Claude Code 等使用路径。",
    audience: ["想用 GPT / Claude 但卡在账号或支付的人", "需要 API Key / token / 中转配置的人", "需要把 Claude Code 或 Gemini 跑起来的人"],
    commonNeeds: ["账号注册与订阅路径判断", "API Key 获取与环境配置", "Claude Code 授权与模型接入", "模型选择、费用路径和替代方案比较", "提示词、工作流和最小调用 demo"],
    deliverables: ["可执行配置步骤", "最小可运行示例或配置截图", "风险与限制说明", "必要时远程协助完成配置", "后续排查建议"],
    requiredMaterials: ["你所在地区和可用付款方式", "遇到的报错截图", "想使用的平台或模型", "目标用途和预算", "是否方便远程协助"],
    priceRange: "50-300 元起，复杂账号/环境问题另估",
    timeline: "小问题当天，复杂环境 1-3 天",
    risks: ["第三方平台风控可能变化", "不承诺绕过平台审核", "不接盗号、破解、批量滥用"],
    cases: [
      { title: "Claude Code 授权跑不通", description: "检查账号、网络、模型渠道和本地环境变量，给到可复用配置。" },
      { title: "OpenAI API 使用问题", description: "确认 key、余额、代理和 SDK 配置，跑通一个最小请求。" }
    ],
    faq: [
      { question: "账号开通一定成功吗？", answer: "不保证。酷里会先判断可行路径和风险，不承诺平台审核结果。" },
      { question: "能远程帮我配吗？", answer: "可以，前提是你确认账号风险和隐私边界。" }
    ]
  },
  {
    slug: "document-processing",
    title: "文档与文件急救",
    tag: "文档处理",
    summary: "处理 PDF、Word、PPT、Excel、翻译、排版、格式转换、合并拆分和报错文件。",
    audience: ["急着交材料但格式乱的人", "需要 PDF 翻译保留排版的人", "有批量文件处理需求的人"],
    commonNeeds: ["PDF 翻译保排版", "Word/PPT 格式修复", "Excel 表格清洗整理", "OCR/扫描件整理", "文件合并、拆分、转换、压缩"],
    deliverables: ["处理后的文档文件", "转换前后说明", "无法完全还原处的说明", "必要的操作步骤", "可复用的批处理建议"],
    requiredMaterials: ["原始文件", "目标格式或语言", "截止时间", "样例或格式要求", "是否允许调整版式以保证可读性"],
    priceRange: "50-300 元常见，扫描件/复杂排版另估",
    timeline: "小文档当天，复杂文档 1-3 天",
    risks: ["扫描件和复杂公式可能无法完美还原", "低质量源文件会影响效果", "版权或敏感材料需你自行确认可处理"],
    cases: [
      { title: "论文 PDF 翻译保排版", description: "先检查页数、扫描质量和公式比例，再给翻译和排版方案。" },
      { title: "Word 格式急救", description: "统一标题、目录、页眉页脚、图片和表格布局。" }
    ],
    faq: [
      { question: "可以保留原排版吗？", answer: "尽量保留。扫描件、复杂公式和图片文字会提前说明风险。" },
      { question: "能不能先看文件再报价？", answer: "可以，文件越完整越容易判断工作量。" }
    ]
  },
  {
    slug: "tool-development",
    title: "小工具与网页 demo",
    tag: "小工具开发",
    summary: "把一句想法做成能看的网页、小程序原型、课程项目 demo 或自动化脚本。",
    audience: ["需要课程项目或作品集 demo 的人", "想把重复工作自动化的人", "需要简单后台或展示页的人"],
    commonNeeds: ["网页 demo", "课程项目页面", "自动化脚本", "简单后台和数据展示", "表单收集、文件处理和小型工作流"],
    deliverables: ["可运行源码或静态页面", "本地运行说明", "核心截图或演示链接", "数据结构说明", "后续扩展建议"],
    requiredMaterials: ["你想展示的核心功能", "参考图或草稿", "数据样例", "截止时间和交付格式", "是否需要部署上线"],
    priceRange: "150-1000 元常见，完整系统另拆范围",
    timeline: "原型 1-3 天，复杂功能按阶段估",
    risks: ["第一版优先可演示，不默认包含长期维护", "部署上线、二次开发另算", "需求不清会先做范围拆解"],
    cases: [
      { title: "课程项目网页 demo", description: "做首页、表单、列表和后台截图感，适合先给老师或队友看。" },
      { title: "批量处理脚本", description: "把重复改名、表格整理、图片压缩做成一次性脚本。" }
    ],
    faq: [
      { question: "能做完整 App 吗？", answer: "可以先拆成原型或技术验证，再决定是否继续做完整项目。" },
      { question: "会交源码吗？", answer: "按约定交付。小 demo 通常会附运行说明。" }
    ]
  },
  {
    slug: "deployment-config",
    title: "部署与远程配置",
    tag: "部署配置",
    summary: "帮你处理服务器、域名、数据库、环境变量、代理网络和远程排查。",
    audience: ["上线前环境卡住的人", "不会配服务器和域名的人", "本地能跑但线上挂掉的人"],
    commonNeeds: ["服务器部署", "域名与证书", "数据库和环境变量", "代理网络排查", "构建失败、日志和监控排查"],
    deliverables: ["部署结果或排查结论", "关键配置记录", "风险和维护说明", "回滚/重启建议", "必要时远程操作"],
    requiredMaterials: ["服务器面板或 SSH 信息", "项目源码或仓库", "域名/数据库信息", "错误日志截图", "可接受的停机窗口和权限边界"],
    priceRange: "100-800 元常见，长时间排查另估",
    timeline: "简单部署当天，复杂问题 1-3 天",
    risks: ["账号权限和费用由你确认", "不默认长期托管", "敏感凭证需临时授权并及时更换"],
    cases: [
      { title: "Vercel/服务器部署失败", description: "检查构建命令、环境变量、端口和日志。" },
      { title: "域名和 HTTPS 配置", description: "配置解析、证书和反向代理，确认访问链路。" }
    ],
    faq: [
      { question: "需要给密码吗？", answer: "尽量用临时权限或远程共享；完成后建议更换敏感凭证。" },
      { question: "包含后续维护吗？", answer: "默认不包含。后续环境变化和迁移作为新需求。" }
    ]
  },
  {
    slug: "api-token",
    title: "API Key / token",
    tag: "API",
    summary: "围绕 OpenAI、Claude、模型中转站、低价 token 和 SDK 调用做配置咨询。",
    audience: ["有 key 但不会接入的人", "想比较模型渠道的人", "本地 SDK 调不通的人"],
    commonNeeds: ["API Key 配置", "中转站接入", "SDK 最小示例", "调用报错排查", "额度、计费、模型名和 baseURL 梳理"],
    deliverables: ["可运行最小调用示例", "配置路径说明", "渠道风险提示", "错误排查记录", "后续接入建议"],
    requiredMaterials: ["目标模型或平台", "现有 key 或渠道", "报错日志", "使用场景", "预算和稳定性要求"],
    priceRange: "50-300 元起",
    timeline: "多数当天完成",
    risks: ["渠道稳定性不由酷里保证", "费用和合规由你确认", "不接滥用平台的需求"],
    cases: [
      { title: "Node/Python SDK 跑通", description: "配置 key、baseURL 和模型名，跑通一次请求。" },
      { title: "模型渠道比较", description: "按预算、速度和稳定性给出选择建议。" }
    ],
    faq: [
      { question: "能提供低价渠道吗？", answer: "可以聊可行渠道和风险，但不保证第三方长期稳定。" },
      { question: "能帮我管 key 吗？", answer: "不建议长期托管你的 key；只做配置和排查。" }
    ]
  },
  {
    slug: "not-sure",
    title: "不知道怎么分",
    tag: "先聊聊",
    summary: "说不清也可以，直接截图、描述卡住的地方，酷里会帮你继续拆问题。",
    audience: ["不知道需求属于哪类的人", "只有截图或一句想法的人", "想先问能不能做的人"],
    commonNeeds: ["需求判断", "范围拆解", "初步报价", "下一步建议", "通用任务、临时咨询和不知道怎么表达的问题"],
    deliverables: ["问题归类", "可行路径", "大致报价", "需要补充的材料清单", "是否先免费判断或进入正式订单的建议"],
    requiredMaterials: ["你当前卡住的截图", "想达到的效果", "截止时间", "预算区间", "任何 Excel、Word、PDF、图片或报错文件"],
    priceRange: "先免费判断，确认可做后报价",
    timeline: "通常当天回复",
    risks: ["描述越模糊越需要追问", "无法判断风险时不会直接开工", "违法违规需求不会接"],
    cases: [
      { title: "只有一句想法", description: "先拆成能交付的小任务，再判断报价和周期。" },
      { title: "只有报错截图", description: "先判断错误属于工具、账号、网络还是代码问题。" }
    ],
    faq: [
      { question: "我不会描述怎么办？", answer: "直接截图，加一句“我现在卡在这里”就行。" },
      { question: "先问问要钱吗？", answer: "初步判断不收费；确认要做才报价。" }
    ]
  }
];

export function findService(slug: string) {
  return serviceCatalog.find((service) => service.slug === slug);
}

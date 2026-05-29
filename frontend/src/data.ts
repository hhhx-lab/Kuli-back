import { Bot, Code2, FileText, Globe2, KeyRound, ServerCog, Sparkles, Wrench } from "lucide-react";

export const services = [
  {
    slug: "ai-tools",
    icon: Bot,
    title: "GPT / Claude / Google 相关",
    description: "账号注册、订阅开通、API Key、Claude Code 授权、Gemini 使用问题。",
    tag: "AI 工具"
  },
  {
    slug: "document-processing",
    icon: FileText,
    title: "文档与文件急救",
    description: "PDF 翻译保格式、表格整理、格式转换、论文/报告格式急救。",
    tag: "文档处理"
  },
  {
    slug: "tool-development",
    icon: Code2,
    title: "小工具与网页 demo",
    description: "网页、小程序、课程项目 demo、自动化脚本，先做能看的试跑版本。",
    tag: "小工具开发"
  },
  {
    slug: "deployment-config",
    icon: ServerCog,
    title: "部署与远程配置",
    description: "服务器部署、域名、数据库、代理网络、远程协助排查。",
    tag: "部署配置"
  },
  {
    slug: "api-token",
    icon: KeyRound,
    title: "API Key / token",
    description: "OpenAI、Claude、模型中转站、低价 token 与配置路径咨询。",
    tag: "API"
  },
  {
    slug: "not-sure",
    icon: Wrench,
    title: "不知道怎么分",
    description: "直接截图，加一句“我现在卡在这里”，酷里会继续追问。",
    tag: "先聊聊"
  }
];

export const cases = [
  ["AI 工具", "帮学生把 GPT / Claude 使用路径理顺", "确认地区、付款方式、账号风险和替代方案，给到可执行步骤。"],
  ["PDF", "论文 PDF 翻译后尽量保持原排版", "先看页数、扫描质量和公式比例；复杂页会提前说明可能变形。"],
  ["网页 demo", "把一句想法做成能看的网页原型", "先做核心页面、按钮状态和提交反馈，后续部署和维护另算。"],
  ["部署", "服务器、域名、环境变量卡住", "通过截图和远程信息判断问题，涉及敏感数据时先讲风险。"],
  ["脚本", "批量改名、表格整理、图片压缩", "把重复手工活变成一次性小脚本，交付时说明怎么跑。"]
];

export const faqItems = [
  ["scope", "我不会描述需求，可以直接发截图吗？", "可以。直接截图，加一句“我现在卡在这里”；酷里会根据截图继续追问。"],
  ["payment", "小需求真的可以验收后付款吗？", "范围清楚、工作量较小、风险可控时可以。复杂需求会先拆范围，必要时收定金。"],
  ["payment", "定金一般什么时候需要？", "需要开发、部署、远程排查、多轮沟通或占用较长时间时，可能先收定金。"],
  ["delivery", "交付物会是什么？", "可能是处理好的文件、配置步骤、可运行网页、脚本、部署结果或问题排查结论。"],
  ["scope", "能做完整 App 或长期项目吗？", "酷里更适合短期轻量需求。完整 App 可以先拆成 demo / 原型 / 技术验证。"],
  ["risk", "账号开通和订阅一定成功吗？", "不保证。第三方平台规则、地区、支付和风控会变化，酷里只能先判断可行路径和风险。"],
  ["delivery", "默认包含后续维护吗？", "不包含。交付后环境变化、功能新增、重新部署、二次修改，都作为新需求另算。"],
  ["risk", "哪些需求酷里不会接？", "违法违规、绕过安全限制、盗号、破解、批量滥用平台、风险不可控的需求不会接。"]
];

export const statusLabels: Record<string, { label: string; hint: string; icon: typeof Sparkles }> = {
  submitted: { label: "已提交", hint: "小纸条已经进窗口", icon: Sparkles },
  clarifying: { label: "需求确认中", hint: "酷里正在看需求", icon: Globe2 },
  quoted: { label: "已报价", hint: "请确认报价范围", icon: KeyRound },
  deposit_pending: { label: "等定金", hint: "复杂需求先定金", icon: ServerCog },
  in_progress: { label: "处理中", hint: "正在开发或处理", icon: Code2 },
  review: { label: "待验收", hint: "等你反馈效果", icon: FileText },
  final_payment_pending: { label: "等尾款", hint: "交付验收后结尾款", icon: Bot },
  completed: { label: "已完成", hint: "交付完成", icon: Sparkles },
  cancelled: { label: "已取消", hint: "需求停止处理", icon: Wrench }
};

export const serviceIconBySlug = Object.fromEntries(services.map((service) => [service.slug, service.icon]));

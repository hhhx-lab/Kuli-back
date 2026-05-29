import { getService } from "./database.js";

export type AgentBriefInput = {
  demand: string;
  category: string;
  serviceSlug: string;
  urgency: string;
  budget: string;
  attachmentCount?: number;
};

const keywordMap = [
  ["Excel", ["excel", "表格", "xlsx", "csv"]],
  ["PDF", ["pdf", "扫描", "论文"]],
  ["图片", ["图片", "截图", "照片", "png", "jpg"]],
  ["AI 工具", ["gpt", "claude", "gemini", "api", "token", "key"]],
  ["部署", ["部署", "服务器", "域名", "环境变量"]],
  ["网页/工具", ["网页", "demo", "脚本", "自动化", "小程序"]]
] as const;

export function polishDemand(input: { demand: string; serviceSlug?: string }) {
  const demand = clean(input.demand);
  const service = input.serviceSlug ? getService(input.serviceSlug) : undefined;
  const tags = extractTags(demand);
  const serviceText = service ? `这件事大概属于「${service.title}」。` : "我还不确定它属于哪一类。";
  return {
    polishedDemand: `${serviceText}我想先判断能不能帮我处理：${demand}。如果可以，希望你们告诉我需要补充哪些材料、预计周期、是否收费以及大概报价。`,
    hints: buildHints(demand, tags)
  };
}

export function createAgentBrief(input: AgentBriefInput) {
  const demand = clean(input.demand);
  const tags = extractTags(demand);
  const service = getService(input.serviceSlug);
  const consultationFirst = /咨询|先问|看看|能不能|不知道|不确定|先报价/.test(`${demand}${input.budget}${input.category}`);
  return {
    originalDemand: demand,
    summary: `用户想${consultationFirst ? "先咨询并判断可行性" : "推进一个可交付需求"}，方向是${service?.title ?? input.category}，涉及${tags.length ? tags.join("、") : "通用任务"}。`,
    tags,
    suggestedQuestions: buildQuestions(input, tags),
    recommendedNextStatus: consultationFirst ? "clarifying" : "quoted",
    consultationFirst,
    chargeHint: consultationFirst ? "先免费判断是否能做；确认要交付或深入排查后再报价。" : "需要先明确交付范围，再决定验收后付款或定金。"
  };
}

function clean(value: string) {
  return value.trim().replace(/\s+/g, " ");
}

function extractTags(demand: string) {
  const lower = demand.toLowerCase();
  return keywordMap.filter(([, words]) => words.some((word) => lower.includes(word.toLowerCase()))).map(([label]) => label);
}

function buildHints(demand: string, tags: string[]) {
  const hints = ["补充截止时间", "上传相关文件或截图"];
  if (!/[0-9一二三四五六七八九十]+.*(页|个|份|张|行|列)/.test(demand)) hints.push("说明文件数量或页面规模");
  if (tags.includes("AI 工具")) hints.push("说明账号、地区、报错截图和可接受风险");
  if (tags.includes("部署")) hints.push("补充服务器、域名和错误日志");
  return hints;
}

function buildQuestions(input: AgentBriefInput, tags: string[]) {
  const questions = ["最终想得到什么交付物？", "希望什么时候完成？"];
  if (input.attachmentCount) questions.push(`已收到 ${input.attachmentCount} 个附件，需要确认是否齐全。`);
  if (tags.includes("Excel")) questions.push("表格是否有固定模板、字段或输出格式要求？");
  if (tags.includes("PDF")) questions.push("PDF 是否包含扫描页、公式或需要保留原排版？");
  if (tags.includes("图片")) questions.push("图片是否需要识别文字、整理内容或只作为问题截图？");
  if (input.budget.includes("先报价")) questions.push("是否接受先免费判断，确认范围后再报价？");
  return questions;
}

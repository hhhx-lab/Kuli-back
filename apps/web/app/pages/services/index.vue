<template>
  <section class="shell page-hero">
    <p class="eyebrow">能做什么 / 怎么帮我</p>
    <h1 class="mega">不是万能客服，是一支会先帮你<em>拆问题</em>的小队。</h1>
    <p class="lead">遇到临时卡住的小事，可以先丢给酷里看看。能说明白最好；说不清也没关系，我们会帮你把关键点一点点问出来。</p>
  </section>

  <section class="shell section" id="services">
    <div class="section-head">
      <h2>酷里可以帮你的事</h2>
      <p>不用先分得很准，先把卡住的地方发来，酷里会帮你判断下一步。</p>
    </div>
    <div class="grid">
      <NuxtLink v-for="(service, index) in services" :key="service.slug" class="card service-card" :class="{ featured: service.slug === 'not-sure' }" :to="`/services/${service.slug}`">
        <div>
          <div class="iconbox">{{ service.slug === "not-sure" ? "?" : String(index + 1).padStart(2, "0") }}</div>
          <h3>{{ service.title }}</h3>
          <p>{{ service.summary }}</p>
        </div>
        <ul class="inline-list">
          <li v-for="need in service.commonNeeds.slice(0, 3)" :key="need" class="chip">{{ need }}</li>
        </ul>
      </NuxtLink>
    </div>
  </section>

  <section class="shell section" id="cases">
    <div class="section-head">
      <h2>几个常见小活样子</h2>
      <p>这些是判断参考，不是固定商品。酷里会先看你的具体情况。</p>
    </div>
    <div class="grid">
      <article v-for="item in caseCards" :key="item.title" class="card case-card" :class="{ featured: item.featured }">
        <div class="tag-row">
          <span v-for="tag in item.tags" :key="tag" class="chip">{{ tag }}</span>
        </div>
        <div>
          <h3>{{ item.title }}</h3>
          <p>{{ item.description }}</p>
        </div>
        <footer>
          <span>{{ item.fit }}</span>
          <strong>{{ item.settlement }}</strong>
        </footer>
      </article>
      <article class="card case-card featured">
        <div class="sticky-note"><strong>不用先写清楚方案</strong>直接截图，加一句“我现在卡在这里”，就可以作为第一张小纸条。</div>
        <NuxtLink class="button" to="/note">丢张小纸条给酷里看看</NuxtLink>
      </article>
    </div>
  </section>

  <section class="shell section split-band" id="rules">
    <article class="panel window quote-panel">
      <div class="window-bar"><span class="dot red" /><span class="dot yellow" /><span class="dot green" /><span>rule.note</span></div>
      <blockquote>小需求可以验收后付款；复杂需求先收定金。</blockquote>
      <cite>默认不包长期售后，后续维护、部署、修改另算。</cite>
    </article>
    <div class="timeline">
      <div class="timeline-item"><span class="step-num">1</span><div><strong>先判断</strong><p>你把材料发来，酷里先看能不能做、风险在哪里。</p></div></div>
      <div class="timeline-item"><span class="step-num">2</span><div><strong>再报价</strong><p>范围清楚后给大致价格；说不清的会继续追问。</p></div></div>
      <div class="timeline-item"><span class="step-num">3</span><div><strong>确认验收方式</strong><p>交付什么、怎么判断完成、是否需要部署，先讲明白。</p></div></div>
      <div class="timeline-item"><span class="step-num">4</span><div><strong>交付后结清</strong><p>小活可验收后付款；定金项目按约定节点结算。</p></div></div>
    </div>
  </section>

  <section class="shell section">
    <table class="price-table" aria-label="结算方式说明">
      <thead>
        <tr><th>情况</th><th>怎么结算</th><th>适合例子</th></tr>
      </thead>
      <tbody>
        <tr><td>小需求</td><td>验收后付款</td><td>PDF 处理、配置指导、简单脚本、轻量页面修改</td></tr>
        <tr><td>复杂需求</td><td>先付定金，节点验收</td><td>网页 demo、部署上线、远程排查、多轮修改</td></tr>
        <tr><td>后续维护</td><td>作为新需求另算</td><td>功能新增、环境迁移、二次部署、长期托管</td></tr>
      </tbody>
    </table>
  </section>

  <section class="shell section" id="faq">
    <div class="section-head">
      <h2>常见问题</h2>
      <p>点分类过滤，先把付款、范围、交付和风险看清楚。</p>
    </div>
    <div class="faq-tools" aria-label="FAQ 分类过滤">
      <button v-for="item in faqFilters" :key="item.value" class="faq-filter" :class="{ 'is-active': faqFilter === item.value }" type="button" @click="faqFilter = item.value">
        {{ item.label }}
      </button>
    </div>
    <div class="faq">
      <details v-for="item in visibleFaq" :key="item.question" :open="faqFilter !== 'all' || item.open">
        <summary>{{ item.question }}</summary>
        <p>{{ item.answer }}</p>
      </details>
    </div>
  </section>
</template>

<script setup lang="ts">
const api = useApi();
const { data } = await useAsyncData("services", () => api.listServices());
const services = computed(() => data.value?.services ?? []);

const caseCards = [
  {
    title: "帮学生把 GPT / Claude 使用路径理顺",
    description: "确认地区、付款方式、账号风险和替代方案，给到可执行步骤；不承诺代替平台审核。",
    tags: ["AI 工具", "账号开通"],
    fit: "适合：不懂技术但想先用起来",
    settlement: "先问",
    featured: true
  },
  {
    title: "论文 PDF 翻译后尽量保持原排版",
    description: "先看页数、扫描质量和公式比例；能自动化就自动化，复杂页会提前说明可能变形。",
    tags: ["PDF", "翻译排版"],
    fit: "适合：急交材料",
    settlement: "验收后付"
  },
  {
    title: "把一句想法做成能看的网页原型",
    description: "先做核心页面、按钮状态和提交反馈，不堆复杂后台；后续部署和维护另算。",
    tags: ["网页 demo", "课程项目"],
    fit: "适合：先给老师或队友看",
    settlement: "可定金"
  },
  {
    title: "服务器、域名、环境变量卡住",
    description: "通过截图和远程信息判断问题；涉及账号权限、付费服务、敏感数据时会先讲风险。",
    tags: ["部署", "远程配置"],
    fit: "适合：临时上线前救急",
    settlement: "先拆范围"
  },
  {
    title: "批量改名、表格整理、图片压缩",
    description: "把重复手工活变成一次性小脚本；交付时说明怎么跑、哪里不要乱改。",
    tags: ["脚本", "批处理"],
    fit: "适合：一次性效率需求",
    settlement: "小活"
  }
];

const faqFilters = [
  { label: "全部", value: "all" },
  { label: "付款", value: "payment" },
  { label: "范围", value: "scope" },
  { label: "交付", value: "delivery" },
  { label: "风险", value: "risk" }
] as const;

const faqFilter = ref<(typeof faqFilters)[number]["value"]>("all");
const faqItems = [
  { topic: "scope", question: "我不会描述需求，可以直接发截图吗？", answer: "可以。直接截图，加一句“我现在卡在这里”；如果知道想达到什么效果，也可以顺手写上。酷里会根据截图继续追问。", open: true },
  { topic: "payment", question: "小需求真的可以验收后付款吗？", answer: "范围清楚、工作量较小、风险可控时可以。复杂需求会先拆范围，必要时收定金。" },
  { topic: "payment", question: "定金一般什么时候需要？", answer: "需要开发、部署、远程排查、多轮沟通、占用较长时间，或涉及第三方付费平台时，可能先收定金。" },
  { topic: "delivery", question: "交付物会是什么？", answer: "取决于需求：可能是处理好的文件、配置步骤、可运行网页、脚本、部署结果或问题排查结论。" },
  { topic: "scope", question: "能做完整 App 或长期项目吗？", answer: "酷里更适合短期轻量需求。完整 App 或长期项目可以先拆成 demo / 原型 / 技术验证，再决定是否继续。" },
  { topic: "risk", question: "账号开通和订阅一定成功吗？", answer: "不保证。第三方平台规则、地区、支付和风控会变化，酷里只能先判断可行路径和风险。" },
  { topic: "delivery", question: "默认包含后续维护吗？", answer: "不包含。交付后环境变化、功能新增、重新部署、二次修改，都作为新需求另算。" },
  { topic: "risk", question: "哪些需求酷里不会接？", answer: "违法违规、绕过安全限制、盗号、破解、批量滥用平台、需要敏感账号密码且风险不可控的需求不会接。" }
];

const visibleFaq = computed(() => faqItems.filter((item) => faqFilter.value === "all" || item.topic === faqFilter.value));

useKuliSeo({
  title: "酷里服务详情 | AI 工具、文档处理、小工具开发和部署配置",
  description: "查看酷里可承接的服务类型、常见需求、结算方式、交付边界和风险说明，适合先判断问题能不能做、材料够不够。",
  path: "/services",
  structuredData: computed(() => [
    faqPageJsonLd(faqItems.slice(0, 5).map((item) => ({ question: item.question, answer: item.answer })))
  ])
});
</script>

<template>
  <section v-if="service" class="shell page-hero service-detail-hero">
    <NuxtLink class="back-link" to="/services">返回服务列表</NuxtLink>
    <p class="eyebrow">{{ service.tag }}</p>
    <h1 class="mega">{{ service.title }}</h1>
    <p class="lead">{{ service.summary }}</p>
    <div class="hero-actions">
      <NuxtLink class="button" :to="`/note?service=${service.slug}`">带着这个服务写小纸条</NuxtLink>
      <a class="button secondary" href="#detail-faq">先看常见问题</a>
    </div>
  </section>

  <section v-if="service" class="shell section detail-intro">
    <article class="panel window quote-panel">
      <div class="window-bar"><span class="dot red" /><span class="dot yellow" /><span class="dot green" /><span>{{ service.slug }}.note</span></div>
      <blockquote>先判断能不能做，再讲清楚怎么交付。</blockquote>
      <cite>{{ service.priceRange }} · {{ service.timeline }}</cite>
    </article>
    <div class="timeline">
      <div class="timeline-item"><span class="step-num">1</span><div><strong>适合人群</strong><p>{{ service.audience.join("；") }}</p></div></div>
      <div class="timeline-item"><span class="step-num">2</span><div><strong>你先提供材料</strong><p>{{ service.requiredMaterials.slice(0, 3).join("、") }}</p></div></div>
      <div class="timeline-item"><span class="step-num">3</span><div><strong>酷里确认范围</strong><p>确认交付物、风险边界、报价和验收方式。</p></div></div>
    </div>
  </section>

  <section v-if="service" class="shell section">
    <div class="section-head">
      <h2>点进来以后，先看这几件事。</h2>
      <p>每个服务详情都按同一套结构展示，避免用户只看到一个空泛服务名。</p>
    </div>
    <div class="detail-grid">
      <section>
        <span class="chip">常见需求</span>
        <h2>你可能想解决</h2>
        <ul><li v-for="item in service.commonNeeds" :key="item">{{ item }}</li></ul>
      </section>
      <section>
        <span class="chip">交付物</span>
        <h2>最后能拿到</h2>
        <ul><li v-for="item in service.deliverables" :key="item">{{ item }}</li></ul>
      </section>
      <section>
        <span class="chip">材料清单</span>
        <h2>你需要准备</h2>
        <ul><li v-for="item in service.requiredMaterials" :key="item">{{ item }}</li></ul>
      </section>
      <section>
        <span class="chip">风险边界</span>
        <h2>先说清楚</h2>
        <ul><li v-for="item in service.risks" :key="item">{{ item }}</li></ul>
      </section>
    </div>
  </section>

  <section v-if="service" class="shell section">
    <div class="section-head">
      <h2>参考案例</h2>
      <p>不是固定套餐，是酷里判断范围和风险时的参考样子。</p>
    </div>
    <div class="grid">
      <article v-for="item in service.cases" :key="item.title" class="card case-card featured">
        <div class="tag-row"><span class="chip">{{ service.tag }}</span><span class="chip">{{ service.timeline }}</span></div>
        <div><h3>{{ item.title }}</h3><p>{{ item.description }}</p></div>
        <footer><span>适合：{{ service.audience[0] }}</span><strong>先拆范围</strong></footer>
      </article>
      <article class="card case-card">
        <div class="sticky-note"><strong>不知道怎么说也行</strong>直接把截图、文件、报错和想达到的效果丢过来。</div>
        <NuxtLink class="button" :to="`/note?service=${service.slug}`">开始写小纸条</NuxtLink>
      </article>
    </div>
  </section>

  <section v-if="service" id="detail-faq" class="shell section">
    <div class="section-head">
      <h2>这个服务的 FAQ</h2>
      <p>先把价格、周期、交付和限制讲清楚，减少来回沟通。</p>
    </div>
    <div class="faq">
      <details v-for="item in service.faq" :key="item.question" open>
        <summary>{{ item.question }}</summary>
        <p>{{ item.answer }}</p>
      </details>
      <details>
        <summary>价格和周期怎么定？</summary>
        <p>{{ service.priceRange }}；{{ service.timeline }}。如果需求不清楚，酷里会先追问材料和验收方式。</p>
      </details>
      <details>
        <summary>提交小纸条后会发生什么？</summary>
        <p>酷里会先归类、判断材料是否足够，再进入报价、定金、执行、验收或取消。</p>
      </details>
    </div>
  </section>

  <section v-if="service" class="shell section detail-cta">
    <div>
      <p class="eyebrow">Ready?</p>
      <h2>把这个问题先丢给酷里看看。</h2>
      <p class="lead">你不用写方案，只要告诉我们现在卡在哪里、想达到什么效果、能提供哪些材料。</p>
    </div>
    <NuxtLink class="button" :to="`/note?service=${service.slug}`">带入“{{ service.tag }}”写小纸条</NuxtLink>
  </section>
</template>

<script setup lang="ts">
const route = useRoute();
const api = useApi();
const { data } = await useAsyncData(`service-${route.params.slug}`, () => api.getService(String(route.params.slug)));
const service = computed(() => data.value?.service);
const seoTitle = computed(() => (service.value ? `${service.value.title} | 酷里服务详情` : "酷里服务详情"));
const seoDescription = computed(() => (
  service.value
    ? `${service.value.summary} 酷里会先确认材料、交付物、价格周期参考和风险边界，再推进小纸条与订单沟通。`
    : "查看酷里服务详情、材料清单、交付物、价格周期参考、风险说明和常见问题。"
));
const seoPath = computed(() => `/services/${String(route.params.slug)}`);
const serviceFaq = computed(() => {
  if (!service.value) return [];
  return [
    ...service.value.faq.map((item) => ({ question: item.question ?? "", answer: item.answer ?? "" })),
    {
      question: "价格和周期怎么定？",
      answer: `${service.value.priceRange}；${service.value.timeline}。如果需求不清楚，酷里会先追问材料和验收方式。`
    },
    {
      question: "提交小纸条后会发生什么？",
      answer: "酷里会先归类、判断材料是否足够，再进入报价、定金、执行、验收或取消。"
    }
  ];
});

useKuliSeo({
  title: seoTitle,
  description: seoDescription,
  path: seoPath,
  structuredData: computed(() => (serviceFaq.value.length ? [faqPageJsonLd(serviceFaq.value)] : []))
});
</script>

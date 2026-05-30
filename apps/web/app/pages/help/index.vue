<template>
  <section class="shell page-hero">
    <p class="eyebrow">酷里知识库</p>
    <h1 class="mega">不知道怎么问，就先从这里<em>翻一翻</em>。</h1>
    <p class="lead">这里和小酷使用同一套公开业务知识：服务说明、材料要求、收费边界、订单状态和安全规则。</p>
    <div class="hero-actions">
      <NuxtLink class="button" to="/note">直接写小纸条</NuxtLink>
      <NuxtLink class="button secondary" to="/services">看服务详情</NuxtLink>
    </div>
  </section>

  <section class="shell section two-col">
    <aside class="panel window knowledge-search">
      <div class="window-bar"><span class="dot red" /><span class="dot yellow" /><span class="dot green" /><span>knowledge.find</span></div>
      <div class="field">
        <label for="knowledge-search">搜一个卡住的点</label>
        <input id="knowledge-search" v-model="searchText" type="search" placeholder="例如：PDF、定金、订单状态、材料">
      </div>
      <div class="choice-row">
        <label v-for="item in scopeFilters" :key="item.value">
          <input v-model="scope" type="radio" name="scope" :value="item.value">
          <span>{{ item.label }}</span>
        </label>
      </div>
      <div class="sticky-note">
        <strong>小酷也看这里</strong>页面、FAQ 和小酷回答都从这份知识源延伸，避免一个地方一个说法。
      </div>
    </aside>

    <div class="knowledge-results">
      <article v-for="item in filteredArticles" :key="item.id" class="card knowledge-card">
        <div class="tag-row">
          <span class="chip">{{ scopeLabel(item.scope) }}</span>
          <span v-for="tag in item.tags.slice(0, 3)" :key="tag" class="chip">{{ tag }}</span>
        </div>
        <h2>{{ item.title }}</h2>
        <p>{{ item.body }}</p>
        <footer>
          <span>{{ item.source }}</span>
          <NuxtLink v-if="serviceSlug(item.source)" class="chip" :to="`/services/${serviceSlug(item.source)}`">看详情 →</NuxtLink>
        </footer>
      </article>
      <article v-if="!filteredArticles.length" class="notice">
        <strong>没有匹配</strong>
        <span>换个说法试试，或者直接写小纸条让酷里继续追问。</span>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { KnowledgeArticle } from "~/composables/useApi";

const api = useApi();
const { data } = await useAsyncData("knowledge", () => api.listKnowledge());
const articles = computed(() => data.value?.articles ?? []);
const searchText = ref("");
const scope = ref("all");

const scopeFilters = [
  { label: "全部", value: "all" },
  { label: "服务", value: "service" },
  { label: "规则", value: "rule" },
  { label: "FAQ", value: "faq" },
  { label: "安全", value: "safety" }
];

const filteredArticles = computed(() => {
  const query = searchText.value.trim().toLowerCase();
  return articles.value.filter((item) => {
    const inScope = scope.value === "all" || item.scope === scope.value;
    if (!inScope) return false;
    if (!query) return true;
    const haystack = `${item.title}\n${item.body}\n${item.tags.join(" ")}`.toLowerCase();
    return haystack.includes(query);
  });
});

function scopeLabel(value: KnowledgeArticle["scope"]) {
  const match = scopeFilters.find((item) => item.value === value);
  return match?.label ?? value;
}

function serviceSlug(source: string) {
  return source.startsWith("service:") ? source.replace("service:", "") : "";
}

useKuliSeo({
  title: "酷里文档中心 | 快速开始、核心概念、FAQ 和指南",
  description: "酷里文档中心收录快速开始、核心概念、常见问题、指南和联系我们说明，并作为小酷 Agent 的公开业务知识来源。",
  path: "/help"
});
</script>

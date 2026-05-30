<template>
  <section class="shell docs-layout">
    <aside class="docs-sidebar">
      <NuxtLink class="back-link" to="/help">← 文档中心</NuxtLink>
      <strong>文档目录</strong>
      <NuxtLink
        v-for="item in docs"
        :key="item.slug"
        :class="{ active: item.slug === doc?.slug }"
        :to="`/help/${item.slug}`"
      >
        <span>{{ item.title }}</span>
        <small>{{ item.description }}</small>
      </NuxtLink>
    </aside>

    <article v-if="doc" class="doc-reader">
      <p class="eyebrow">{{ doc.category }}</p>
      <h1>{{ doc.title }}</h1>
      <p class="lead">{{ doc.description }}</p>
      <div class="tag-row">
        <span v-for="tag in doc.tags" :key="tag" class="chip">{{ tag }}</span>
        <span class="chip">更新 {{ doc.updatedAt }}</span>
      </div>
      <div class="doc-body" v-html="htmlContent" />
      <footer class="doc-related">
        <strong>继续阅读</strong>
        <NuxtLink v-for="item in doc.relatedDocs" :key="item.slug" class="chip" :to="`/help/${item.slug}`">{{ item.title }}</NuxtLink>
      </footer>
    </article>

    <aside v-if="doc" class="doc-toc">
      <strong>本页目录</strong>
      <a v-for="anchor in doc.anchors" :key="anchor.id" :href="`#${anchor.id}`">{{ anchor.title }}</a>
      <NuxtLink class="button secondary" to="/note">写小纸条</NuxtLink>
    </aside>
  </section>
</template>

<script setup lang="ts">
import type { DocDetail, DocSummary } from "~/composables/useApi";

const route = useRoute();
const api = useApi();
const slug = computed(() => String(route.params.slug));
const { data: docsData } = await useAsyncData("docs-nav", () => api.listDocs());
const { data: docData, error } = await useAsyncData(`doc-${slug.value}`, () => api.getDoc(slug.value));

if (error.value) {
  throw createError({ statusCode: 404, statusMessage: "文档不存在" });
}

const docs = computed<DocSummary[]>(() => docsData.value?.docs ?? []);
const doc = computed<DocDetail | null>(() => docData.value?.doc ?? null);
const htmlContent = computed(() => markdownToHtml(doc.value?.content ?? ""));
const faqStructuredData = computed(() => {
  if (doc.value?.slug !== "faq") return [];
  const entries = markdownFaqItems(doc.value.content);
  return entries.length ? [faqPageJsonLd(entries)] : [];
});

useKuliSeo({
  title: computed(() => (doc.value ? `${doc.value.title} | 酷里文档中心` : "酷里文档中心")),
  description: computed(() => (
    doc.value
      ? `${doc.value.description} 阅读酷里文档中心，了解服务范围、订单规则、材料准备、付款验收和安全边界。`
      : "阅读酷里文档中心，了解服务范围、订单规则、材料准备、付款验收和安全边界。"
  )),
  path: computed(() => `/help/${slug.value}`),
  structuredData: faqStructuredData
});

function markdownToHtml(markdown: string) {
  const lines = markdown.split("\n");
  const html: string[] = [];
  let listOpen = false;

  function closeList() {
    if (listOpen) {
      html.push("</ul>");
      listOpen = false;
    }
  }

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      closeList();
      continue;
    }

    const heading = line.match(/^(#{2,4})\s+(.+?)(?:\s+\{#([a-z0-9-]+)\})?$/);
    if (heading) {
      closeList();
      const level = Math.min(4, heading[1]?.length ?? 2);
      const title = heading[2] ?? "";
      const id = heading[3] ?? title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
      html.push(`<h${level} id="${escapeHtml(id)}">${escapeHtml(title)}</h${level}>`);
      continue;
    }

    if (line.startsWith("- ")) {
      if (!listOpen) {
        html.push("<ul>");
        listOpen = true;
      }
      html.push(`<li>${escapeHtml(line.slice(2))}</li>`);
      continue;
    }

    closeList();
    html.push(`<p>${escapeHtml(line)}</p>`);
  }

  closeList();
  return html.join("");
}

function escapeHtml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function markdownFaqItems(markdown: string) {
  const lines = markdown.split("\n");
  const entries: Array<{ question: string; answer: string }> = [];
  let currentQuestion = "";
  let currentAnswer: string[] = [];

  function flush() {
    if (currentQuestion && currentAnswer.length) {
      entries.push({ question: currentQuestion, answer: currentAnswer.join(" ").trim() });
    }
    currentQuestion = "";
    currentAnswer = [];
  }

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line || line === "---" || line.includes(":")) continue;
    const heading = line.match(/^##\s+(.+?)(?:\s+\{#[a-z0-9-]+\})?$/);
    if (heading) {
      flush();
      currentQuestion = heading[1] ?? "";
      continue;
    }
    if (currentQuestion && !line.startsWith("#")) currentAnswer.push(line.replace(/^- /, ""));
  }
  flush();
  return entries;
}
</script>

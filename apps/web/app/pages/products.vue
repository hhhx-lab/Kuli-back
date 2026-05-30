<template>
  <section class="shell products-hero">
    <div>
      <p class="eyebrow">Products</p>
      <h1 class="mega">酷里的工具和子产品，会从这里慢慢上线。</h1>
      <p class="lead">这里是公开产品导航页，只展示可用入口和上线计划，不读取本机项目目录，也不接真实项目管理。</p>
    </div>
    <div class="product-console">
      <span class="status-dot" />
      <strong>product.routes</strong>
      <p>先做服务入口，再逐步补工具。</p>
    </div>
  </section>

  <section class="shell section product-board">
    <article v-for="item in products" :key="item.title" class="product-tile" :class="item.status">
      <div class="tag-row">
        <span class="chip">{{ statusLabel[item.status] }}</span>
        <span class="chip">{{ item.kind }}</span>
      </div>
      <h2>{{ item.title }}</h2>
      <p>{{ item.description }}</p>
      <div class="product-actions">
        <NuxtLink class="button" :to="item.to">{{ item.cta }}</NuxtLink>
        <NuxtLink class="button secondary" :to="item.docs">查看说明</NuxtLink>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
type ProductStatus = "available" | "beta" | "planned";

const statusLabel: Record<ProductStatus, string> = {
  available: "可用",
  beta: "内测",
  planned: "即将上线"
};

const products: Array<{ title: string; description: string; kind: string; status: ProductStatus; to: string; docs: string; cta: string }> = [
  {
    title: "酷里小纸条",
    description: "把一句模糊需求整理成订单线索，适合先判断能不能做、材料够不够。",
    kind: "订单入口",
    status: "available",
    to: "/note",
    docs: "/help/quick-start",
    cta: "写小纸条"
  },
  {
    title: "小酷 Agent",
    description: "3D 小猫服务助手，帮助用户理解服务、整理需求、解释订单状态。",
    kind: "服务助手",
    status: "beta",
    to: "/help/concepts",
    docs: "/help/guides",
    cta: "了解小酷"
  },
  {
    title: "文档处理工具箱",
    description: "面向 PDF、PPT、表格和批量处理的轻量工具集合，后续逐步上线。",
    kind: "效率工具",
    status: "planned",
    to: "/services/document-processing",
    docs: "/help/faq",
    cta: "看相关服务"
  },
  {
    title: "部署检查清单",
    description: "给服务器、域名、环境变量、对象存储和上线前 smoke 的辅助检查入口。",
    kind: "上线辅助",
    status: "planned",
    to: "/services/deployment-config",
    docs: "/help/guides",
    cta: "查看部署服务"
  }
];

useKuliSeo({
  title: "酷里产品与工具箱 | 小纸条、小酷 Agent 和效率工具",
  description: "酷里产品页展示小纸条、小酷 Agent、文档处理工具箱和部署检查清单等公开工具入口，方便用户找到适合当前需求的服务路径。",
  path: "/products"
});
</script>

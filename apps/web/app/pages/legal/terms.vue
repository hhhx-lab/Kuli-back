<template>
  <section class="section legal-page">
    <div class="legal-hero terms">
      <p class="eyebrow">Agreement</p>
      <h1>服务条款</h1>
      <p>酷里先帮你把需求说清楚，再由管理员确认范围、报价、付款方式和交付边界。</p>
    </div>

    <div class="legal-layout">
      <aside class="legal-nav">
        <NuxtLink to="/legal/privacy">隐私政策</NuxtLink>
        <NuxtLink to="/legal/terms">服务条款</NuxtLink>
        <NuxtLink to="/legal/upload-policy">上传说明</NuxtLink>
      </aside>

      <article class="legal-document">
        <h2>咨询与报价</h2>
        <p>提交小纸条和基础咨询不等于平台已承诺接单。具体能否做、多少钱、多久完成，需要管理员基于材料和风险确认。</p>

        <h2>小酷的边界</h2>
        <p>小酷可以解释服务、整理需求、提醒补材料和说明订单状态。小酷不代表最终报价，不承诺周期，不替管理员做最终承诺。</p>

        <h2>付款与验收</h2>
        <p>小需求可以约定验收后付款，复杂需求可能需要先付定金。定金、尾款、验收节点和修改范围以订单中的管理员公开说明为准。</p>

        <h2>售后与修改</h2>
        <p>交付后的修改以订单约定为准。默认不包含长期维护、账号托管、部署监控、第三方平台长期适配或无限次修改。</p>

        <h2>不接的需求</h2>
        <p>违法违规、破解绕过、盗号、批量滥用平台、索要敏感凭证或风险不可控的需求，酷里会拒绝处理。</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
useKuliSeo({
  title: "服务条款 | 酷里 Kuli",
  description: "阅读酷里服务条款，了解咨询、报价、定金、尾款、验收、售后修改和小酷 Agent 的业务边界。",
  path: "/legal/terms"
});
</script>

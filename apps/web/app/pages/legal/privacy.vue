<template>
  <section class="section legal-page">
    <div class="legal-hero">
      <p class="eyebrow">Legal</p>
      <h1>隐私政策</h1>
      <p>这份说明用于公开发布版本，帮助你理解酷里会收集什么、为什么需要这些信息，以及这些信息不会被怎样使用。</p>
    </div>

    <div class="legal-layout">
      <aside class="legal-nav">
        <NuxtLink to="/legal/privacy">隐私政策</NuxtLink>
        <NuxtLink to="/legal/terms">服务条款</NuxtLink>
        <NuxtLink to="/legal/upload-policy">上传说明</NuxtLink>
      </aside>

      <article class="legal-document">
        <h2>我们会收集的信息</h2>
        <p>酷里会为了账号登录、订单沟通和交付保存你的邮箱、展示名、订单内容、附件 metadata、小酷对话摘要、访问日志和必要的安全审计记录。</p>

        <h2>这些信息如何使用</h2>
        <p>信息只用于判断服务范围、推进订单、发送通知、回答与酷里业务相关的问题、保护账号安全，以及改进服务流程。</p>

        <h2>我们不会做什么</h2>
        <p>酷里不出售个人数据，不向其他用户展示你的订单、附件、沟通内容、付款记录或小酷对话。</p>

        <h2>AI 与订单边界</h2>
        <p>小酷回答基于酷里知识库、当前页面和你自己的订单摘要。小酷不会读取其他用户订单，也不代表最终报价、周期或管理员承诺。</p>

        <h2>删除与处理请求</h2>
        <p>如果你需要处理、导出或删除自己的账号与订单数据，可以通过联系我们页面发起请求。涉及交付、对账和安全审计的信息可能需要按必要周期保留。</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
useKuliSeo({
  title: "隐私政策 | 酷里 Kuli",
  description: "了解酷里如何收集和使用邮箱、订单内容、附件 metadata、小酷对话摘要和访问日志，以及普通用户订单与附件的权限边界。",
  path: "/legal/privacy"
});
</script>

<template>
  <section class="section legal-page">
    <div class="legal-hero upload">
      <p class="eyebrow">Upload Policy</p>
      <h1>文件上传与敏感信息说明</h1>
      <p>上传材料是为了让管理员判断需求和交付范围，不是为了让用户暴露账号、支付或身份凭证。</p>
    </div>

    <div class="legal-layout">
      <aside class="legal-nav">
        <NuxtLink to="/legal/privacy">隐私政策</NuxtLink>
        <NuxtLink to="/legal/terms">服务条款</NuxtLink>
        <NuxtLink to="/legal/upload-policy">上传说明</NuxtLink>
      </aside>

      <article class="legal-document">
        <h2>建议上传什么</h2>
        <p>可以上传截图、PDF、Word、PPT、表格、报错文本、参考链接、旧版本文件和你希望参考的风格材料。文件名尽量清楚，方便管理员判断。</p>

        <h2>不要直接上传什么</h2>
        <p>请不要在小纸条、附件或小酷对话中直接发送密码、验证码、私钥、支付凭证、身份证等敏感信息。</p>

        <h2>账号类需求怎么处理</h2>
        <p>如果确实涉及账号类操作，先描述目标和遇到的问题。后续由管理员单独确认安全方式，例如临时授权、远程协助或操作完成后及时更换凭证。</p>

        <h2>附件权限</h2>
        <p>普通用户只能访问自己订单下的公开附件。管理员可以为处理订单查看必要附件；内部备注、成本、利润和后台标签不会展示给普通用户。</p>

        <h2>小酷不会索要敏感信息</h2>
        <p>小酷会提醒你不要提交敏感凭证，也不会要求你发送密码、验证码、私钥或支付凭证。</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
useKuliSeo({
  title: "文件上传与敏感信息说明 | 酷里 Kuli",
  description: "了解酷里订单附件和小纸条材料的上传建议、敏感信息边界、账号类需求处理方式和小酷不会索要密码验证码的规则。",
  path: "/legal/upload-policy"
});
</script>

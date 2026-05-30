<template>
  <section class="shell hero">
    <div>
      <p class="eyebrow">AI 创客小队 · 小需求急救</p>
      <h1>搞不动？先丢给<em>酷里</em>看看。</h1>
      <p class="lead">文件处理不了、AI 工具不会配置、GPT / Google / Claude 服务不会开通、小程序网页想做 demo、服务器部署卡住，都可以先从一张小纸条开始。</p>
      <div class="hero-actions">
        <NuxtLink class="button" to="/note">丢张小纸条给酷里看看</NuxtLink>
        <NuxtLink class="button secondary" to="/services">看看能帮什么</NuxtLink>
      </div>
    </div>
    <div class="panel window">
      <div class="window-bar"><span class="dot red" /><span class="dot yellow" /><span class="dot green" /><span>$ kuli ask</span></div>
      <div class="chat-line me"><div class="bubble">我想开 GPT Pro，但不知道怎么弄。</div></div>
      <div class="chat-line"><span class="avatar">K</span><div class="bubble">先把你在哪、用什么账号、方便怎么付说一下就好；小活确认能做，做好你看过再结。</div></div>
      <div class="chat-line me"><div class="bubble">还有一个 PDF 想翻译，格式不要乱。</div></div>
      <div class="chat-line"><span class="avatar">K</span><div class="bubble">把文件和目标语言一起丢过来，我们先判断工作量。</div></div>
      <p class="sketch">直接截图：我现在卡在这里</p>
    </div>
  </section>

  <section class="shell section">
    <div class="section-head">
      <h2>最近大家问得最多的，都在这了。</h2>
      <p>不是标准商品列表，更像一扇小窗口：先说问题，酷里判断能不能做、怎么做、多少钱。</p>
    </div>
    <div class="grid">
      <article class="card service-card featured">
        <div><div class="iconbox">AI</div><h3>GPT / Claude / Google 相关</h3><p>账号注册、订阅开通、API Key、Claude Code 授权、Gemini 使用问题。</p></div>
        <NuxtLink class="chip" to="/note?service=ai-tools">我想先问问 →</NuxtLink>
      </article>
      <article class="card service-card">
        <div><div class="iconbox">PDF</div><h3>文档与文件急救</h3><p>PDF 翻译保格式、表格整理、批量改名、压缩包与报错文件排查。</p></div>
        <NuxtLink class="chip" to="/services/document-processing">查看说明 →</NuxtLink>
      </article>
      <article class="card service-card">
        <div><div class="iconbox">&lt;/&gt;</div><h3>小工具与网页 demo</h3><p>小程序、网页、课程项目 demo、自动化脚本，先做能看的试跑版本。</p></div>
        <NuxtLink class="chip" to="/note?service=tool-development">说说想法 →</NuxtLink>
      </article>
      <article class="card service-card">
        <div><div class="iconbox">SSH</div><h3>部署与远程配置</h3><p>服务器部署、域名、数据库、代理网络、远程协助排查。</p></div>
        <NuxtLink class="chip" to="/services/deployment-config">看规则 →</NuxtLink>
      </article>
      <article class="card service-card">
        <div><div class="iconbox">?</div><h3>不知道归哪类</h3><p>描述不清也没关系，直接截图，加一句“我现在卡在这里”，酷里会继续追问。</p></div>
        <NuxtLink class="chip" to="/note?service=not-sure">直接写纸条 →</NuxtLink>
      </article>
      <article class="card service-card">
        <div class="sticky-note"><strong>小活当天搞定</strong>大一点的需求先拆范围，再决定是否收定金。</div>
      </article>
    </div>
  </section>

  <section class="shell section">
    <div class="section-head">
      <h2>酷里怎么做</h2>
      <p>流程尽量轻，不把一次临时求助变成复杂项目。</p>
    </div>
    <div class="grid">
      <article class="card process-card"><span class="step-num">1</span><h3>你先说需求</h3><p>写几句话、发截图或文件，告诉我们你想解决什么。</p></article>
      <article class="card process-card"><span class="step-num">2</span><h3>酷里判断能不能做</h3><p>评估可行性、工作量、风险和大致报价。</p></article>
      <article class="card process-card"><span class="step-num">3</span><h3>小需求验收后付款</h3><p>能快速交付的任务，确认效果后再付款。</p></article>
      <article class="card process-card"><span class="step-num">4</span><h3>复杂需求先定金</h3><p>需要开发、部署或多轮沟通时，可能先收一部分定金。</p></article>
    </div>
    <article class="notice">
      <strong>提醒</strong>
      <span>默认不包长期售后。后续部署、维护、修改、二次开发会另算。</span>
    </article>
</section>
</template>

<script setup lang="ts">
useKuliSeo({
  title: "酷里 Kuli | AI 工具、文档处理和小工具开发服务",
  description: "酷里帮助用户从一张小纸条开始咨询 AI 工具、文档处理、小工具开发、部署配置和 API/token 相关需求，先判断边界，再推进订单交付。",
  path: "/"
});
</script>

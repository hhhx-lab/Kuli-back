<template>
  <section class="shell section">
    <p class="eyebrow">写张小纸条</p>
    <h1 class="mega">不用写得专业，先把卡住的地方<em>丢过来</em>。</h1>
    <p class="lead">酷里会先判断能不能做、需不需要更多材料、是验收后付款还是先付定金。</p>
  </section>

  <section class="shell section two-col" id="note-form">
    <aside class="panel window">
      <div class="window-bar"><span class="dot red" /><span class="dot yellow" /><span class="dot green" /><span>tips.txt</span></div>
      <div class="sticky-note">
        <strong>可以这样写</strong>
        “我想开通 Google Pro，但是不会弄。”<br>
        “PDF 需要翻译，还要保持排版。”<br>
        “我现在卡在这里。”然后直接配一张截图。
      </div>
      <div class="notice">
        <strong>小贴士</strong>
        <span>不用先写清楚方案。直接截图，加一句“我现在卡在这里”，会更容易判断。</span>
      </div>
    </aside>

    <form class="panel form-panel" @submit.prevent="submit">
      <div class="field">
        <label for="need-detail">1. 你想搞定什么？</label>
        <textarea id="need-detail" v-model="originalDemand" maxlength="800" placeholder="例如：我想开通 GPT Pro，但是不会弄；我有一个 PDF 想翻译并保留格式；我想做一个小程序 / 网页 demo。" />
        <small>{{ originalDemand.length }} / 800</small>
      </div>

      <div class="field">
        <label>2. 大概属于哪一类？</label>
        <div class="choice-row">
          <label v-for="service in services" :key="service.slug">
            <input v-model="serviceSlug" type="radio" name="kind" :value="service.slug">
            <span>{{ service.tag }}</span>
          </label>
        </div>
      </div>

      <button class="button secondary" type="button" @click="polish">让 AI 帮我整理</button>

      <div class="field">
        <label for="polished-demand">3. 整理后的需求</label>
        <textarea id="polished-demand" v-model="demand" placeholder="点上面的按钮，小酷会先帮你整理一版；你也可以自己改。" />
      </div>

      <div v-if="hints.length" class="hint-box">
        <strong>建议补充</strong>
        <span v-for="hint in hints" :key="hint">{{ hint }}</span>
      </div>

      <div class="field">
        <label>4. 什么时候需要？</label>
        <div class="choice-row">
          <label v-for="item in urgencyOptions" :key="item"><input v-model="urgency" type="radio" name="time" :value="item"><span>{{ item }}</span></label>
        </div>
      </div>

      <div class="field">
        <label>5. 预算大概多少？</label>
        <div class="choice-row">
          <label v-for="item in budgetOptions" :key="item"><input v-model="budget" type="radio" name="budget" :value="item"><span>{{ item }}</span></label>
        </div>
      </div>

      <div class="field">
        <label for="contact">6. 怎么联系你？</label>
        <input id="contact" v-model="contact" type="text" placeholder="微信 / QQ / 邮箱都可以">
        <small>只用于沟通，不会对外公开。</small>
      </div>

      <div class="notice">
        <strong>规则说明</strong>
        <span>小活可以先做完再结；大一点的活可能要先付定金。默认不包长期售后，部署 / 维护 / 修改另算。</span>
      </div>
      <div class="notice safety">
        <strong>敏感信息提醒</strong>
        <span>不要提交密码、验证码、私钥、支付凭证、身份证等敏感信息。涉及账号类操作时，后续由管理员确认安全方式。</span>
      </div>
      <button class="button submit-button" type="submit">丢张小纸条给酷里看看</button>
      <div v-if="result" class="status-box is-visible">已提交：{{ result.orderNumber }}，下一步：{{ result.nextAction }}</div>
    </form>
  </section>
</template>

<script setup lang="ts">
const route = useRoute();
const api = useApi();
const { data } = await useAsyncData("note-services", () => api.listServices());
const services = computed(() => data.value?.services ?? []);
const serviceSlug = ref(String(route.query.service ?? "not-sure"));
const originalDemand = ref("");
const demand = ref("");
const contact = ref("");
const urgency = ref("1-2 天");
const budget = ref("先报价看看");
const hints = ref<string[]>([]);
const intent = ref("consultation");
const result = ref<{ orderNumber: string; nextAction: string } | null>(null);
const urgencyOptions = ["今天", "1-2 天", "3-5 天", "不急", "先聊聊"];
const budgetOptions = ["50 元以内", "50-100", "100-300", "300-1000", "先报价看看"];

async function polish() {
  const response = await api.polishDemand({ demand: originalDemand.value, serviceSlug: serviceSlug.value });
  demand.value = response.polishedDemand;
  hints.value = response.hints;
  intent.value = response.intent;
}

async function submit() {
  const auth = useAuthStore();
  await auth.restore();
  const response = await api.createOrder({
    serviceSlug: serviceSlug.value,
    originalDemand: originalDemand.value,
    demand: demand.value || originalDemand.value,
    category: services.value.find((service) => service.slug === serviceSlug.value)?.tag ?? "先聊聊",
    urgency: urgency.value,
    budget: budget.value,
    contact: contact.value,
    intent: intent.value
  }, auth.token);
  result.value = { orderNumber: response.order.orderNumber, nextAction: response.order.nextAction };
}
</script>

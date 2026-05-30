<template>
  <section class="section">
    <NuxtLink class="back-link" to="/admin">返回管理台</NuxtLink>
    <div v-if="!auth.user" class="info-card">
      <strong>需要管理员登录</strong>
      <NuxtLink class="button" to="/login">去登录</NuxtLink>
    </div>
    <div v-else-if="order" class="detail-layout admin-detail">
      <article class="info-card">
        <div class="eyebrow">Admin Order</div>
        <h1>{{ order.orderNumber }}</h1>
        <p>{{ order.title }}</p>
        <strong>{{ order.status }} · {{ order.priority }}</strong>
      </article>

      <section class="info-card">
        <h2>订单内容</h2>
        <p>{{ order.originalDemand }}</p>
        <p class="muted">{{ order.demand }}</p>
        <dl class="meta-list">
          <div><dt>成本</dt><dd>{{ order.cost ?? "未填" }}</dd></div>
          <div><dt>利润</dt><dd>{{ order.profit ?? "未填" }}</dd></div>
          <div><dt>内部备注</dt><dd>{{ order.internalNotes || "无" }}</dd></div>
        </dl>
      </section>

      <section class="info-card">
        <h2>快速维护</h2>
        <div class="form-grid">
          <label>状态
            <select v-model="patch.status">
              <option value="submitted">submitted</option>
              <option value="clarifying">clarifying</option>
              <option value="quoted">quoted</option>
              <option value="deposit_pending">deposit_pending</option>
              <option value="in_progress">in_progress</option>
              <option value="review">review</option>
              <option value="final_payment_pending">final_payment_pending</option>
              <option value="completed">completed</option>
              <option value="cancelled">cancelled</option>
            </select>
          </label>
          <label>优先级
            <select v-model="patch.priority">
              <option value="low">low</option>
              <option value="normal">normal</option>
              <option value="high">high</option>
              <option value="urgent">urgent</option>
            </select>
          </label>
          <label>成本
            <input v-model.number="patch.cost" type="number" min="0" />
          </label>
          <label>利润
            <input v-model.number="patch.profit" type="number" min="0" />
          </label>
        </div>
        <label>下一步
          <input v-model="patch.nextAction" />
        </label>
        <label>客户可见备注
          <textarea v-model="patch.publicNotes" />
        </label>
        <label>内部备注
          <textarea v-model="patch.internalNotes" />
        </label>
        <button class="button" type="button" @click="savePatch">保存维护</button>
      </section>

      <section class="info-card">
        <div class="section-head compact">
          <h2>AI 自动化建议</h2>
          <button class="button secondary" type="button" @click="runAutomation">重新运行自动化</button>
        </div>
        <div v-if="order.automationSuggestions.length" class="stack">
          <article v-for="suggestion in order.automationSuggestions" :key="suggestion.id" class="row-item">
            <span>{{ suggestion.severity }} · {{ suggestion.kind }}</span>
            <strong>{{ suggestion.summary }}</strong>
            <small>建议状态：{{ suggestion.suggestedStatus ?? "无" }} · 置信度：{{ Math.round(suggestion.confidence * 100) }}%</small>
            <button v-if="suggestion.status === 'open'" class="button secondary" type="button" @click="applySuggestion(suggestion.id)">采纳建议</button>
          </article>
        </div>
        <p v-else>暂无建议。</p>
      </section>

      <section class="info-card">
        <h2>待办与 AI 摘要</h2>
        <div class="stack">
          <article v-for="todo in order.todos" :key="todo.id" class="row-item">
            <span>{{ todo.status }} · {{ todo.source }}</span>
            <strong>{{ todo.title }}</strong>
          </article>
          <article v-for="summary in order.aiSummaries" :key="summary.id" class="row-item">
            <span>AI Summary</span>
            <strong>{{ summary.summary }}</strong>
            <small>{{ summary.suggestedQuestions.join("、") }}</small>
          </article>
        </div>
      </section>

      <section class="info-card">
        <h2>沟通</h2>
        <div v-if="order.messages.length" class="stack">
          <article v-for="item in order.messages" :key="item.id" class="row-item">
            <span>{{ item.visibility }} · {{ formatTime(item.createdAt) }}</span>
            <strong>{{ item.body }}</strong>
          </article>
        </div>
        <div class="form-grid">
          <input v-model="adminMessage.body" placeholder="给客户或内部团队的备注" @keyup.enter="sendAdminMessage" />
          <select v-model="adminMessage.visibility">
            <option value="public">客户可见</option>
            <option value="internal">内部备注</option>
          </select>
          <button class="button" type="button" @click="sendAdminMessage">发送</button>
        </div>
      </section>

      <section class="info-card">
        <h2>附件</h2>
        <div v-if="order.attachments.length" class="stack">
          <div v-for="file in order.attachments" :key="file.id" class="row-item">
            <span>{{ file.fileName }}</span>
            <small>{{ file.scanStatus }} · 重试 {{ file.retryCount }} 次 · {{ file.storageKey }}</small>
            <small v-if="file.parsedSummary">{{ file.parsedSummary }}</small>
            <small v-if="file.scanError">解析问题：{{ file.scanError }}</small>
            <small v-if="file.lastScannedAt">最近解析：{{ formatTime(file.lastScannedAt) }}</small>
            <button class="button secondary" type="button" @click="openAttachment(file)">下载</button>
            <button class="button secondary" type="button" @click="retryScan(file)">重试解析</button>
          </div>
        </div>
        <p v-else>暂无附件。</p>
      </section>

      <section class="info-card">
        <h2>报价 / 付款 / 交付</h2>
        <div class="form-grid">
          <input v-model.number="quote.amount" type="number" min="0" placeholder="报价金额" />
          <select v-model="quote.kind">
            <option value="full">全款</option>
            <option value="deposit">定金</option>
            <option value="final">尾款</option>
          </select>
          <input v-model="quote.note" placeholder="报价说明" />
          <button class="button secondary" type="button" @click="addQuote">发报价</button>
        </div>
        <div class="form-grid">
          <input v-model.number="payment.amount" type="number" min="0" placeholder="收款金额" />
          <select v-model="payment.kind">
            <option value="deposit">定金</option>
            <option value="final">尾款</option>
            <option value="full">全款</option>
          </select>
          <select v-model="payment.status">
            <option value="pending">待确认</option>
            <option value="received">已收到</option>
          </select>
          <input v-model="payment.method" placeholder="收款方式" />
          <button class="button secondary" type="button" @click="addPayment">记收款</button>
        </div>
        <div class="form-grid">
          <input v-model="deliverable.title" placeholder="交付物标题" />
          <input v-model="deliverable.storageKey" placeholder="对象存储 key / 链接" />
          <button class="button secondary" type="button" @click="addDeliverable">登记交付</button>
        </div>
        <div v-if="order.quotes.length || order.payments.length || order.deliverables.length" class="stack">
          <article v-for="item in order.quotes" :key="item.id" class="row-item">
            <span>报价 · {{ item.kind }} · {{ item.status }}</span>
            <strong>¥{{ item.amount }}</strong>
            <small>{{ item.note }}</small>
          </article>
          <article v-for="item in order.payments" :key="item.id" class="row-item">
            <span>收款 · {{ item.kind }} · {{ item.status }}</span>
            <strong>¥{{ item.amount }}</strong>
            <small>{{ item.method }} {{ item.note }}</small>
          </article>
          <article v-for="item in order.deliverables" :key="item.id" class="row-item">
            <span>交付物</span>
            <strong>{{ item.title }}</strong>
            <small>{{ item.storageKey }}</small>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { AdminOrder, AdminOrderPatch, OrderAttachment } from "~/composables/useApi";

const route = useRoute();
const auth = useAuthStore();
const api = useApi();
const config = useRuntimeConfig();
const order = ref<AdminOrder | null>(null);
const orderNumber = computed(() => String(route.params.orderNumber));
const patch = reactive<AdminOrderPatch>({});
const adminMessage = reactive<{ body: string; visibility: "public" | "internal" }>({ body: "", visibility: "public" });
const quote = reactive({ amount: 0, kind: "deposit", note: "" });
const payment = reactive({ amount: 0, kind: "deposit", method: "微信/支付宝/银行转账", status: "received", note: "" });
const deliverable = reactive({ title: "", description: "", storageKey: "" });

onMounted(async () => {
  await auth.restore();
  await load();
});

async function load() {
  if (!auth.token) return;
  order.value = (await api.getAdminOrder(auth.token, orderNumber.value)).order;
  syncPatch();
}

async function runAutomation() {
  if (!auth.token) return;
  order.value = (await api.runAutomation(auth.token, orderNumber.value)).order;
  syncPatch();
}

async function savePatch() {
  if (!auth.token) return;
  order.value = (await api.updateAdminOrder(auth.token, orderNumber.value, patch)).order;
  syncPatch();
}

async function applySuggestion(id: string) {
  if (!auth.token) return;
  order.value = (await api.applySuggestion(auth.token, orderNumber.value, id)).order;
  syncPatch();
}

async function sendAdminMessage() {
  if (!auth.token || !adminMessage.body.trim()) return;
  order.value = (await api.addAdminMessage(auth.token, orderNumber.value, { body: adminMessage.body.trim(), visibility: adminMessage.visibility })).order;
  adminMessage.body = "";
}

async function openAttachment(file: OrderAttachment) {
  if (!auth.token) return;
  const response = await api.getAttachmentDownload(auth.token, orderNumber.value, file.id);
  const url = response.download.downloadUrl.startsWith("/")
    ? `${config.public.apiBaseUrl}${response.download.downloadUrl}`
    : response.download.downloadUrl;
  window.open(url, "_blank", "noopener");
}

async function retryScan(file: OrderAttachment) {
  if (!auth.token) return;
  order.value = (await api.retryAttachmentScan(auth.token, orderNumber.value, file.id)).order;
  syncPatch();
}

async function addQuote() {
  if (!auth.token || !quote.amount || !quote.note.trim()) return;
  order.value = (await api.addQuote(auth.token, orderNumber.value, { amount: quote.amount, kind: quote.kind, note: quote.note.trim() })).order;
  quote.amount = 0;
  quote.note = "";
  syncPatch();
}

async function addPayment() {
  if (!auth.token || !payment.amount) return;
  order.value = (await api.addPayment(auth.token, orderNumber.value, { ...payment })).order;
  payment.amount = 0;
  payment.note = "";
  syncPatch();
}

async function addDeliverable() {
  if (!auth.token || !deliverable.title.trim() || !deliverable.storageKey.trim()) return;
  order.value = (await api.addDeliverable(auth.token, orderNumber.value, { ...deliverable })).order;
  deliverable.title = "";
  deliverable.storageKey = "";
  deliverable.description = "";
  syncPatch();
}

function syncPatch() {
  if (!order.value) return;
  patch.status = order.value.status;
  patch.priority = order.value.priority;
  patch.cost = order.value.cost ?? undefined;
  patch.profit = order.value.profit ?? undefined;
  patch.publicNotes = order.value.publicNotes;
  patch.internalNotes = order.value.internalNotes;
  patch.nextAction = order.value.nextAction;
}

function formatTime(value: string) {
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}
</script>

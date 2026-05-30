<template>
  <section class="section">
    <NuxtLink class="back-link" to="/orders">返回我的订单</NuxtLink>
    <div v-if="!auth.user" class="info-card">
      <strong>需要登录</strong>
      <p>登录后才能查看自己的订单详情。</p>
      <NuxtLink class="button" to="/login">去登录</NuxtLink>
    </div>
    <div v-else-if="order" class="detail-layout">
      <article class="info-card">
        <div class="eyebrow">{{ order.status }} · {{ order.intent }}</div>
        <h1>{{ order.title }}</h1>
        <p>{{ order.aiStatus }}</p>
        <strong>下一步：{{ order.nextAction }}</strong>
      </article>

      <section class="info-card">
        <h2>原始需求</h2>
        <p>{{ order.originalDemand }}</p>
        <h2>小酷整理</h2>
        <p>{{ order.demand }}</p>
      </section>

      <section class="info-card">
        <h2>进度时间线</h2>
        <div class="timeline">
          <div v-for="event in order.events" :key="event.id" class="timeline-item">
            <span>{{ event.status }}</span>
            <strong>{{ event.note }}</strong>
            <small>{{ formatTime(event.createdAt) }}</small>
          </div>
        </div>
      </section>

      <section class="info-card">
        <h2>沟通记录</h2>
        <div v-if="order.messages.length" class="stack">
          <article v-for="item in order.messages" :key="item.id" class="row-item">
            <span>{{ formatTime(item.createdAt) }}</span>
            <strong>{{ item.body }}</strong>
          </article>
        </div>
        <p v-else>还没有沟通记录。</p>
        <div class="chat-row">
          <input v-model="messageBody" placeholder="补充说明、链接或验收反馈" @keyup.enter="sendMessage" />
          <button type="button" @click="sendMessage">发送</button>
        </div>
      </section>

      <section class="info-card">
        <h2>附件</h2>
        <div v-if="order.attachments.length" class="stack">
          <div v-for="file in order.attachments" :key="file.id" class="row-item">
            <span>{{ file.fileName }}</span>
            <small>{{ file.scanStatus }} · {{ Math.ceil(file.fileSize / 1024) }} KB</small>
            <small v-if="file.parsedSummary">{{ file.parsedSummary }}</small>
            <small v-if="file.scanError">解析问题：{{ file.scanError }}</small>
            <button class="button secondary" type="button" @click="openAttachment(file)">下载</button>
          </div>
        </div>
        <p v-else>还没有附件。</p>
        <p class="safety-line">附件不要包含密码、验证码、私钥、支付凭证、身份证等敏感信息。</p>
        <label>补充附件 metadata
          <input type="file" @change="onFileChange" />
        </label>
        <button class="button secondary" type="button" :disabled="!selectedFile" @click="attachSelected">登记附件</button>
      </section>

      <section class="info-card">
        <h2>报价与付款</h2>
        <div v-if="order.quotes.length || order.payments.length" class="stack">
          <article v-for="quote in order.quotes" :key="quote.id" class="row-item">
            <span>报价 · {{ quote.kind }}</span>
            <strong>¥{{ quote.amount }}</strong>
            <small>{{ quote.note }}</small>
          </article>
          <article v-for="payment in order.payments" :key="payment.id" class="row-item">
            <span>付款 · {{ payment.kind }}</span>
            <strong>¥{{ payment.amount }} · {{ payment.status }}</strong>
            <small>{{ payment.method }} {{ payment.note }}</small>
          </article>
        </div>
        <p v-else>还没有报价或付款记录。</p>
      </section>

      <section class="info-card">
        <div class="section-head compact">
          <h2>交付物</h2>
          <button class="button" type="button" :disabled="!canAccept" @click="accept">验收通过</button>
        </div>
        <div v-if="order.deliverables.length" class="stack">
          <article v-for="item in order.deliverables" :key="item.id" class="row-item">
            <span>{{ item.title }}</span>
            <strong>{{ item.description || "已上传交付物" }}</strong>
            <small>{{ item.storageKey }}</small>
          </article>
        </div>
        <p v-else>还没有交付物。</p>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { Order, OrderAttachment } from "~/composables/useApi";

const route = useRoute();
const auth = useAuthStore();
const api = useApi();
const config = useRuntimeConfig();
const order = ref<Order | null>(null);
const selectedFile = ref<File | null>(null);
const messageBody = ref("");
const orderNumber = computed(() => String(route.params.orderNumber));
const canAccept = computed(() => order.value?.status === "review");

onMounted(async () => {
  await auth.restore();
  await load();
});

async function load() {
  if (!auth.token) return;
  order.value = (await api.getOrder(auth.token, orderNumber.value)).order;
}

function onFileChange(event: Event) {
  selectedFile.value = (event.target as HTMLInputElement).files?.[0] ?? null;
}

async function attachSelected() {
  if (!auth.token || !selectedFile.value) return;
  const upload = await api.presignUpload(auth.token, {
    orderNumber: orderNumber.value,
    fileName: selectedFile.value.name,
    fileSize: selectedFile.value.size,
    contentType: selectedFile.value.type || "application/octet-stream"
  });
  await api.uploadFile(auth.token, upload.upload, selectedFile.value);
  const checksum = await sha256File(selectedFile.value);
  order.value = (
    await api.addOrderAttachment(auth.token, orderNumber.value, {
      fileName: selectedFile.value.name,
      fileSize: selectedFile.value.size,
      contentType: selectedFile.value.type || "application/octet-stream",
      storageKey: upload.upload.objectKey,
      bucket: upload.upload.bucket,
      checksum
    })
  ).order;
  selectedFile.value = null;
}

async function sha256File(file: File) {
  if (!crypto.subtle) return "";
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function sendMessage() {
  if (!auth.token || !messageBody.value.trim()) return;
  order.value = (await api.addOrderMessage(auth.token, orderNumber.value, messageBody.value.trim())).order;
  messageBody.value = "";
}

async function accept() {
  if (!auth.token) return;
  order.value = (await api.acceptOrder(auth.token, orderNumber.value)).order;
}

async function openAttachment(file: OrderAttachment) {
  if (!auth.token) return;
  const response = await api.getAttachmentDownload(auth.token, orderNumber.value, file.id);
  const url = response.download.downloadUrl.startsWith("/")
    ? `${config.public.apiBaseUrl}${response.download.downloadUrl}`
    : response.download.downloadUrl;
  window.open(url, "_blank", "noopener");
}

function formatTime(value: string) {
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}
</script>

<template>
  <section class="section">
    <div class="section-head">
      <div>
        <div class="eyebrow">Admin 2.0</div>
        <h1>订单管理台</h1>
      </div>
      <NuxtLink v-if="!auth.user" class="button" to="/login">管理员登录</NuxtLink>
    </div>
    <div class="toolbar">
      <input v-model="search" placeholder="搜索订单号、客户、联系方式、需求关键词、附件名" @keyup.enter="load(1)" />
      <select v-model="status" @change="load(1)">
        <option value="">全部状态</option>
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
      <select v-model="intent" @change="load(1)">
        <option value="">全部意图</option>
        <option value="consultation">先咨询</option>
        <option value="quote_request">希望报价</option>
        <option value="ready_to_start">明确开工</option>
      </select>
      <select v-model="service" @change="load(1)">
        <option value="">全部服务</option>
        <option v-for="item in services" :key="item.slug" :value="item.slug">{{ item.tag }}</option>
      </select>
      <button class="button" @click="load(1)">搜索</button>
    </div>
    <div class="toolbar">
      <small>共 {{ pagination.total }} 单 · 第 {{ pagination.page }} 页</small>
      <button class="button secondary" :disabled="pagination.page <= 1" @click="load(pagination.page - 1)">上一页</button>
      <button class="button secondary" :disabled="!pagination.hasMore" @click="load(pagination.page + 1)">下一页</button>
    </div>
    <div class="admin-grid">
      <NuxtLink v-for="order in orders" :key="order.orderNumber" class="order-card" :to="`/admin/orders/${order.orderNumber}`">
        <span>{{ order.status }} · {{ order.priority }}</span>
        <strong>{{ order.orderNumber }} · {{ order.title }}</strong>
        <p>{{ order.aiStatus }}</p>
        <small>下一步：{{ order.nextAction }}</small>
      </NuxtLink>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { AdminOrder } from "~/composables/useApi";

const auth = useAuthStore();
const api = useApi();
const search = ref("");
const status = ref("");
const intent = ref("");
const service = ref("");
const orders = ref<AdminOrder[]>([]);
const pagination = reactive({ page: 1, pageSize: 20, total: 0, hasMore: false });
const { data: serviceData } = await useAsyncData("admin-services", () => api.listServices());
const services = computed(() => serviceData.value?.services ?? []);

onMounted(async () => {
  await auth.restore();
  await load(1);
});

async function load(page = pagination.page) {
  if (!auth.token) return;
  const query = new URLSearchParams();
  if (search.value) query.set("search", search.value);
  if (status.value) query.set("status", status.value);
  if (intent.value) query.set("intent", intent.value);
  if (service.value) query.set("service", service.value);
  query.set("page", String(page));
  query.set("pageSize", String(pagination.pageSize));
  const response = await api.listAdminOrders(auth.token, `?${query}`);
  orders.value = response.orders;
  Object.assign(pagination, response.pagination ?? { page, pageSize: pagination.pageSize, total: response.orders.length, hasMore: false });
}
</script>

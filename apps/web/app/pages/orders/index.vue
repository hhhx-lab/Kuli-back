<template>
  <section class="section">
    <div class="section-head">
      <div>
        <div class="eyebrow">Orders</div>
        <h1>我的订单工作台</h1>
      </div>
      <NuxtLink v-if="!auth.user" class="button" to="/login">先登录</NuxtLink>
    </div>
    <div class="order-list">
      <NuxtLink v-for="order in orders" :key="order.orderNumber" class="order-card" :to="`/orders/${order.orderNumber}`">
        <span>{{ order.status }} · {{ order.intent }}</span>
        <strong>{{ order.orderNumber }} · {{ order.title }}</strong>
        <p>{{ order.aiStatus }}</p>
        <small>下一步：{{ order.nextAction }}</small>
      </NuxtLink>
      <div v-if="auth.user && orders.length === 0" class="empty-state">
        <strong>还没有订单。</strong>
        <p>先写一张小纸条，酷里会帮你判断能不能做、材料够不够，以及后续是验收后付款还是需要先确认定金。</p>
        <div class="empty-actions">
          <NuxtLink class="button" to="/note">写小纸条</NuxtLink>
          <NuxtLink class="button secondary" to="/services">看看服务</NuxtLink>
        </div>
      </div>
      <div v-if="!auth.user" class="empty-state">
        <strong>登录后这里会变成你的订单工作台。</strong>
        <p>你可以查看自己的订单进度、沟通记录、附件、报价、付款记录和交付物。小酷也会在订单页解释当前状态，告诉你下一步该补材料、等报价还是确认验收。</p>
        <div class="empty-actions">
          <NuxtLink class="button" to="/login">登录查看</NuxtLink>
          <NuxtLink class="button secondary" to="/note">先写小纸条</NuxtLink>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { Order } from "~/composables/useApi";

const auth = useAuthStore();
const api = useApi();
const orders = ref<Order[]>([]);

onMounted(async () => {
  await auth.restore();
  if (auth.token) {
    orders.value = (await api.listOrders(auth.token)).orders;
  }
});
</script>

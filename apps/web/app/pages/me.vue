<template>
  <section class="section account-dashboard">
    <div class="account-hero">
      <div>
        <p class="eyebrow">My Kuli</p>
        <h1>你的酷里主页。</h1>
        <p v-if="summary">登录邮箱：{{ summary.profile.email }}</p>
      </div>
      <NuxtLink class="button" to="/note">写新的小纸条</NuxtLink>
    </div>

    <div v-if="summary" class="dashboard-grid">
      <article class="panel profile-panel">
        <span class="chip">账号</span>
        <h2>{{ summary.profile.displayName }}</h2>
        <p>{{ summary.profile.role === "admin" ? "管理员账号" : "普通账号" }}</p>
        <dl>
          <div><dt>邮箱</dt><dd>{{ summary.profile.email }}</dd></div>
          <div><dt>注册时间</dt><dd>{{ formatDate(summary.profile.createdAt) }}</dd></div>
          <div>
            <dt>邮箱验证</dt>
            <dd>
              {{ summary.profile.emailVerifiedAt ? "已验证" : "待验证" }}
              <button v-if="!summary.profile.emailVerifiedAt" class="button secondary inline-button" type="button" :disabled="verificationBusy" @click="requestVerification">
                {{ verificationBusy ? "发送中" : "发送验证邮件" }}
              </button>
            </dd>
          </div>
        </dl>
        <p v-if="verificationMessage" class="form-success">{{ verificationMessage }}</p>
      </article>

      <article class="panel points-panel">
        <span class="chip">积分进度</span>
        <h2>{{ summary.points.current }} / {{ summary.points.nextLevel }}</h2>
        <div class="progress-track"><span :style="{ width: `${summary.points.progress}%` }" /></div>
        <p>邀请注册、完善资料、完成订单都可以作为后续积分来源。</p>
        <NuxtLink class="button secondary" to="/referrals">邀请注册</NuxtLink>
      </article>

      <article class="panel order-summary-panel">
        <span class="chip">我的订单</span>
        <h2>{{ summary.orders.total }} 单</h2>
        <div class="mini-stats">
          <span v-for="(count, status) in summary.orders.byStatus" :key="status">{{ status }} · {{ count }}</span>
        </div>
        <NuxtLink class="button secondary" to="/orders">进入订单工作台</NuxtLink>
      </article>

      <article class="panel notifications-panel">
        <span class="chip">通知</span>
        <h2>{{ unreadCount }} 条未读</h2>
        <p>管理员回复、报价和交付提醒会同步进入通知中心。</p>
        <NuxtLink class="button secondary" to="/notifications">查看通知</NuxtLink>
      </article>
    </div>

    <section v-if="summary" class="section account-section">
      <div class="section-head">
        <h2>最近订单</h2>
        <NuxtLink class="button secondary" to="/orders">全部订单</NuxtLink>
      </div>
      <div class="order-list">
        <NuxtLink v-for="order in summary.recentOrders" :key="order.orderNumber" class="order-card" :to="`/orders/${order.orderNumber}`">
          <span>{{ order.status }}</span>
          <strong>{{ order.orderNumber }} · {{ order.title }}</strong>
          <small>下一步：{{ order.nextAction }}</small>
        </NuxtLink>
        <div v-if="summary.recentOrders.length === 0" class="empty-state">
          <strong>还没有订单。</strong>
          <p>先写一张小纸条，酷里会帮你判断下一步。</p>
        </div>
      </div>
    </section>

    <section v-if="recentNotifications.length" class="section account-section">
      <div class="section-head">
        <h2>最近通知</h2>
        <NuxtLink class="button secondary" to="/notifications">通知中心</NuxtLink>
      </div>
      <div class="notification-strip">
        <NuxtLink v-for="item in recentNotifications" :key="item.id" :to="item.targetUrl || '/notifications'">
          <span>{{ item.status === "unread" ? "未读" : "已读" }}</span>
          <strong>{{ item.title }}</strong>
          <small>{{ item.body }}</small>
        </NuxtLink>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import type { NotificationItem, UserSummary } from "~/composables/useApi";

const auth = useAuthStore();
const api = useApi();
const summary = ref<UserSummary | null>(null);
const recentNotifications = ref<NotificationItem[]>([]);
const verificationBusy = ref(false);
const verificationMessage = ref("");
const unreadCount = computed(() => recentNotifications.value.filter((item) => item.status === "unread").length);

onMounted(async () => {
  await auth.restore();
  if (auth.token) {
    summary.value = (await api.getMySummary(auth.token)).summary;
    recentNotifications.value = (await api.listNotifications(auth.token)).notifications.slice(0, 3);
  }
});

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("zh-CN");
}

async function requestVerification() {
  if (!auth.token) return;
  verificationBusy.value = true;
  verificationMessage.value = "";
  try {
    const result = await api.requestEmailVerification(auth.token);
    verificationMessage.value = result.message;
  } finally {
    verificationBusy.value = false;
  }
}
</script>

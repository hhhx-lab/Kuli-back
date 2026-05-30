<template>
  <section class="section notifications-page">
    <div class="notifications-hero">
      <div>
        <p class="eyebrow">Notifications</p>
        <h1>通知中心</h1>
        <p>订单回复、报价、交付和系统消息都会集中在这里，邮件失败也不影响站内提醒。</p>
      </div>
      <button class="button secondary" type="button" :disabled="!unreadCount" @click="markAllRead">
        全部已读
      </button>
    </div>

    <div class="notification-summary">
      <span>未读 {{ unreadCount }}</span>
      <span>全部 {{ notifications.length }}</span>
    </div>

    <div class="notification-timeline">
      <article v-for="item in notifications" :key="item.id" class="notification-row" :class="{ unread: item.status === 'unread' }">
        <div class="notification-marker" aria-hidden="true" />
        <div class="notification-content">
          <div class="notification-row-head">
            <span>{{ typeLabel(item.type) }}</span>
            <time>{{ formatDate(item.createdAt) }}</time>
          </div>
          <h2>{{ item.title }}</h2>
          <p>{{ item.body }}</p>
          <div class="notification-actions">
            <NuxtLink v-if="item.targetUrl" class="button secondary" :to="item.targetUrl" @click="markRead(item)">查看相关订单</NuxtLink>
            <button v-if="item.status === 'unread'" class="button secondary" type="button" @click="markRead(item)">标记已读</button>
          </div>
        </div>
      </article>

      <div v-if="!loading && notifications.length === 0" class="empty-state">
        <strong>暂时没有通知。</strong>
        <p>当管理员回复、报价或上传交付物时，这里会出现提醒。</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { NotificationItem } from "~/composables/useApi";

const auth = useAuthStore();
const api = useApi();
const notifications = ref<NotificationItem[]>([]);
const loading = ref(true);

const unreadCount = computed(() => notifications.value.filter((item) => item.status === "unread").length);

onMounted(async () => {
  await auth.restore();
  if (!auth.token) return navigateTo("/login?redirect=/notifications");
  await loadNotifications();
});

async function loadNotifications() {
  if (!auth.token) return;
  loading.value = true;
  try {
    notifications.value = (await api.listNotifications(auth.token)).notifications;
  } finally {
    loading.value = false;
  }
}

async function markRead(item: NotificationItem) {
  if (!auth.token || item.status === "read") return;
  const response = await api.markNotificationRead(auth.token, item.id);
  const index = notifications.value.findIndex((entry) => entry.id === item.id);
  if (index >= 0) notifications.value[index] = response.notification;
}

async function markAllRead() {
  if (!auth.token || !unreadCount.value) return;
  await api.markAllNotificationsRead(auth.token);
  await loadNotifications();
}

function typeLabel(type: string) {
  const labels: Record<string, string> = {
    order_message: "订单消息",
    order_status_changed: "状态变化",
    quote_sent: "报价",
    payment_recorded: "付款",
    deliverable_uploaded: "交付物",
    acceptance_requested: "验收",
    referral_rewarded: "邀请积分",
    system: "系统"
  };
  return labels[type] ?? "通知";
}

function formatDate(value: string) {
  return new Date(value).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}
</script>

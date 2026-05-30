<template>
  <div>
    <header class="topbar">
      <div class="shell nav">
        <NuxtLink class="brand" to="/" aria-label="酷里小窗口首页">
          <span class="mark" aria-hidden="true">K</span>
          <span class="brand-name"><strong>酷里 Kuli</strong><span>酷里小窗口</span></span>
        </NuxtLink>
        <nav class="navlinks" aria-label="主导航">
          <NuxtLink to="/services">能做什么</NuxtLink>
          <NuxtLink to="/help">知识库</NuxtLink>
          <NuxtLink to="/products">产品</NuxtLink>
          <NuxtLink to="/note">写小纸条</NuxtLink>
          <NuxtLink to="/orders">我的订单</NuxtLink>
          <NuxtLink v-if="auth.user?.role === 'admin'" to="/admin">管理后台</NuxtLink>
        </nav>
        <div class="nav-actions">
          <NuxtLink v-if="!auth.user" class="button secondary" to="/login">登录 / 注册</NuxtLink>
          <details v-else class="account-menu">
            <summary>
              <span>{{ auth.user.email }}</span>
              <strong>{{ auth.user.role === "admin" ? "管理员" : "账号" }}</strong>
              <i v-if="unreadCount" class="notification-badge" aria-label="未读通知">{{ unreadCount }}</i>
            </summary>
            <div class="account-popover">
              <NuxtLink to="/me">个人主页</NuxtLink>
              <NuxtLink to="/orders">我的订单</NuxtLink>
              <NuxtLink to="/notifications">通知中心<span v-if="unreadCount">{{ unreadCount }}</span></NuxtLink>
              <NuxtLink to="/settings">设置</NuxtLink>
              <NuxtLink to="/referrals">积分与邀请</NuxtLink>
              <NuxtLink v-if="auth.user.role === 'admin'" to="/admin">管理后台</NuxtLink>
              <button class="button secondary" type="button" @click="logout">退出登录</button>
            </div>
          </details>
          <NuxtLink class="button" to="/note">丢张小纸条给酷里看看</NuxtLink>
        </div>
      </div>
    </header>
    <main>
      <slot />
    </main>
    <footer class="site-footer">
      <div class="shell">
        <span>酷里 Kuli</span>
        <nav aria-label="法律与服务说明">
          <NuxtLink to="/legal/privacy">隐私政策</NuxtLink>
          <NuxtLink to="/legal/terms">服务条款</NuxtLink>
          <NuxtLink to="/legal/upload-policy">上传说明</NuxtLink>
          <NuxtLink to="/help/contact">联系我们</NuxtLink>
        </nav>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
const auth = useAuthStore();
const router = useRouter();
const api = useApi();
const unreadCount = ref(0);

onMounted(async () => {
  await auth.restore();
  await refreshUnreadCount();
});

watch(
  () => auth.token,
  async () => {
    await refreshUnreadCount();
  }
);

async function refreshUnreadCount() {
  if (!auth.token) {
    unreadCount.value = 0;
    return;
  }
  try {
    unreadCount.value = (await api.getUnreadNotificationCount(auth.token)).unreadCount;
  } catch {
    unreadCount.value = 0;
  }
}

async function logout() {
  auth.logout();
  unreadCount.value = 0;
  await router.push("/");
}
</script>

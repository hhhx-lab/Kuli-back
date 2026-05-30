<template>
  <section class="section form-shell settings-page">
    <div>
      <p class="eyebrow">Settings</p>
      <h1>账号设置。</h1>
      <p>第一版只开放展示名修改。邮箱、密码找回、二次验证会放到后续安全批次。</p>
    </div>

    <form class="form" @submit.prevent="save">
      <label>邮箱<input :value="profile?.email ?? ''" disabled /></label>
      <label>展示名<input v-model="displayName" /></label>
      <button class="button" type="submit">保存设置</button>
      <button class="button secondary" type="button" @click="logout">退出登录</button>
      <p v-if="message" class="status-box is-visible">{{ message }}</p>
    </form>
  </section>
</template>

<script setup lang="ts">
import type { UserProfile } from "~/composables/useApi";

const auth = useAuthStore();
const api = useApi();
const router = useRouter();
const profile = ref<UserProfile | null>(null);
const displayName = ref("");
const message = ref("");

onMounted(async () => {
  await auth.restore();
  if (!auth.token) return;
  profile.value = (await api.getProfile(auth.token)).profile;
  displayName.value = profile.value.displayName;
});

async function save() {
  if (!auth.token) return;
  profile.value = (await api.updateProfile(auth.token, { displayName: displayName.value })).profile;
  if (auth.user) auth.user.displayName = profile.value.displayName;
  message.value = "设置已保存";
}

async function logout() {
  auth.logout();
  await router.push("/");
}
</script>

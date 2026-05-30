<template>
  <section class="section referral-page">
    <div class="section-head">
      <div>
        <p class="eyebrow">Referral</p>
        <h1>邀请朋友来酷里。</h1>
        <p>第一版积分只用于成长展示，不做支付抵扣。邀请注册成功后会记录积分奖励。</p>
      </div>
      <NuxtLink class="button secondary" to="/me">回个人主页</NuxtLink>
    </div>

    <div v-if="referral" class="referral-layout">
      <article class="panel referral-card">
        <span class="chip">邀请码</span>
        <h2>{{ referral.referralCode }}</h2>
        <p>{{ inviteUrl }}</p>
        <button class="button" type="button" @click="copyInvite">复制邀请链接</button>
      </article>
      <article class="panel points-panel">
        <span class="chip">积分</span>
        <h2>{{ referral.points }}</h2>
        <p>已奖励邀请：{{ referral.rewardedInvites }} 人</p>
      </article>
      <article class="panel referral-history">
        <h2>奖励记录</h2>
        <div v-if="referral.rewards.length" class="stack">
          <div v-for="item in referral.rewards" :key="item.id" class="row-item">
            <strong>+{{ item.points }}</strong>
            <span>{{ item.reason }} · {{ formatDate(item.createdAt) }}</span>
          </div>
        </div>
        <p v-else>暂时还没有邀请奖励。</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { UserReferral } from "~/composables/useApi";

const auth = useAuthStore();
const api = useApi();
const referral = ref<UserReferral | null>(null);
const inviteUrl = computed(() => {
  if (!referral.value) return "";
  if (import.meta.server) return referral.value.invitePath;
  return `${location.origin}${referral.value.invitePath}`;
});

onMounted(async () => {
  await auth.restore();
  if (auth.token) referral.value = (await api.getReferral(auth.token)).referral;
});

async function copyInvite() {
  if (!inviteUrl.value) return;
  await navigator.clipboard?.writeText(inviteUrl.value);
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("zh-CN");
}
</script>

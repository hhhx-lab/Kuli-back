<template>
  <section class="section form-shell auth-page">
    <div class="auth-copy">
      <div class="eyebrow">Account</div>
      <h1>{{ mode === "login" ? "回到你的酷里窗口。" : "先开一个酷里账号。" }}</h1>
      <p>
        {{ mode === "login" ? "登录后可以写小纸条、查看订单进度、继续和小酷沟通。" : "注册后会自动登录，并回到你刚才想去的页面。" }}
      </p>
      <div class="notice">
        <strong>公开注册</strong>
        <span>注册只会创建普通账号；管理员账号不从这里创建。</span>
      </div>
    </div>

    <form class="form auth-form" @submit.prevent="submit">
      <div class="segmented">
        <button class="button secondary" :class="{ active: mode === 'login' }" type="button" @click="mode = 'login'">登录</button>
        <button class="button secondary" :class="{ active: mode === 'register' }" type="button" @click="mode = 'register'">注册</button>
      </div>
      <label v-if="mode === 'register'">展示名<input v-model="displayName" autocomplete="name" /></label>
      <label>邮箱<input v-model="email" autocomplete="email" /></label>
      <label>密码<input v-model="password" type="password" autocomplete="current-password" /></label>
      <label v-if="mode === 'register'">邀请码<input v-model="referralCode" placeholder="可选" /></label>
      <button class="button" type="submit">{{ mode === "login" ? "登录" : "注册并进入" }}</button>
      <button v-if="mode === 'login'" class="link-button" type="button" @click="showResetRequest = !showResetRequest">忘记密码？</button>
      <p v-if="error" class="form-error">{{ error }}</p>
      <p v-if="notice" class="form-success">{{ notice }}</p>
      <small>登录或注册后可以继续写小纸条、查看订单进度和接收站内通知。</small>

      <div v-if="showResetRequest" class="auth-assist">
        <label>重置邮箱<input v-model="resetEmail" autocomplete="email" placeholder="输入注册邮箱" /></label>
        <button class="button secondary" type="button" @click="requestReset">发送重置邮件</button>
      </div>

      <div v-if="resetToken" class="auth-assist">
        <label>新密码<input v-model="resetPassword" type="password" autocomplete="new-password" placeholder="至少 8 位，包含字母和数字" /></label>
        <button class="button secondary" type="button" @click="confirmReset">确认重置密码</button>
      </div>
    </form>
  </section>
</template>

<script setup lang="ts">
import { ApiError } from "~/composables/useApi";

const auth = useAuthStore();
const api = useApi();
const route = useRoute();
const router = useRouter();
const mode = ref<"login" | "register">("login");
const email = ref("demo@kuli.local");
const password = ref("KuliUser123!");
const displayName = ref("");
const referralCode = ref(String(route.query.referralCode ?? ""));
const error = ref("");
const notice = ref("");
const showResetRequest = ref(false);
const resetEmail = ref("");
const resetPassword = ref("");
const resetToken = ref(String(route.query.resetToken ?? ""));

onMounted(async () => {
  await auth.restore();
  if (route.query.verifyToken) await confirmVerification(String(route.query.verifyToken));
  if (resetToken.value) showResetRequest.value = false;
  if (auth.user && route.query.redirect) await router.replace(String(route.query.redirect));
});

useKuliSeo({
  title: "登录或注册 | 酷里 Kuli",
  description: "使用邮箱和密码登录酷里，登录后可以写小纸条、查看自己的订单进度、接收通知并继续和小酷沟通。",
  path: "/login"
});

async function submit() {
  error.value = "";
  try {
    if (mode.value === "login") {
      await auth.login(email.value, password.value);
    } else {
      await auth.register({
        email: email.value,
        password: password.value,
        displayName: displayName.value || email.value.split("@")[0] || "酷里用户",
        referralCode: referralCode.value || undefined
      });
    }
    const fallback = auth.user?.role === "admin" ? "/admin" : "/orders";
    await router.push(String(route.query.redirect ?? fallback));
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "提交失败，请稍后再试";
  }
}

async function confirmVerification(token: string) {
  error.value = "";
  try {
    const result = await api.confirmEmailVerification({ token });
    notice.value = result.message;
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "邮箱验证失败，请重新发送验证邮件";
  }
}

async function requestReset() {
  error.value = "";
  notice.value = "";
  try {
    const result = await api.requestPasswordReset(resetEmail.value || email.value);
    notice.value = result.message;
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "重置邮件发送失败，请稍后再试";
  }
}

async function confirmReset() {
  error.value = "";
  notice.value = "";
  try {
    const result = await api.confirmPasswordReset({ token: resetToken.value, password: resetPassword.value });
    notice.value = result.message;
    resetToken.value = "";
    resetPassword.value = "";
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "密码重置失败，请重新申请";
  }
}
</script>

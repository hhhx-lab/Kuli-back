<template>
  <NuxtLayout>
    <NuxtPage />
    <XiaokuAvatar v-if="config.public.enableXiaoku" />
  </NuxtLayout>
</template>

<script setup lang="ts">
const config = useRuntimeConfig();

useHead({
  htmlAttrs: { lang: "zh-CN" }
});
</script>

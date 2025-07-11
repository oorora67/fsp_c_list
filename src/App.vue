<template>
  <router-view />
</template>

<script setup>
// ルートはrouter-viewのみ
</script>

<style scoped>
.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}
h1,
h2 {
  margin-top: 1em;
  color: #1976d2;
  text-shadow: 0 1px 4px #e3f2fd;
}
</style>

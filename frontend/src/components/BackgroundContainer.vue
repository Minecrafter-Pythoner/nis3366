<template>
    <div class="min-h-screen bg-blue-900">
      <div class="background-container">
        <slot></slot>
        <router-view/>
      </div>
    </div>
  </template>

<script>
export default {
    name: 'BackgroundContainer'
};
</script>

<style scoped>
.background-container {
    background-image: url('@/assets/background.png');
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
    min-height: 100vh;
    /* 确保背景覆盖整个视口高度 */
    padding: 2rem;
    /* 添加适当的内边距 */
}
</style>

<template>
  <router-view v-slot="{ Component, route }">
    <Transition name="fade" mode="out-in">
      <component :is="Component" :key="route.path" v-if="Component" />
    </Transition>
  </router-view>
</template>

<script setup>
// Simple fade transition - no complex logic that could cause issues
</script>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

<template>
  <p v-if="text" class="preview-help">{{ text }}</p>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.preview-help {
  margin: 4px 0 0;
  font-size: 11px;
  color: #64748b;
}
</style>

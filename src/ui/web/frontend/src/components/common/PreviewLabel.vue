<template>
  <label v-if="label" class="preview-label">
    {{ label }}
    <span v-if="required" class="required-mark">*</span>
  </label>
</template>

<script setup>
defineProps({
  label: {
    type: String,
    default: ''
  },
  required: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.preview-label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #94a3b8;
  margin-bottom: 6px;
}

.required-mark {
  color: #ef4444;
  margin-left: 2px;
}
</style>

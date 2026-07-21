<template>
  <CommonStatusBadge
    :status="status"
    variant="trace"
    :show-icon="true"
    v-bind="$attrs"
  />
</template>

<script setup>
/**
 * Traces StatusBadge - Wrapper for common StatusBadge
 * Supports: completed, success, failed, error, running, pending, cancelled
 * Always shows icons
 */
import CommonStatusBadge from '@/components/common/StatusBadge.vue'

defineProps({
  status: {
    type: String,
    required: true
  }
})
</script>

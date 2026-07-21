<template>
  <div class="pinned-badge" :class="{ 'pinned-badge--compact': compact }" :title="$t('workflow.pinnedData')">
    <Pin :size="compact ? 10 : 12" />
  </div>
</template>

<script setup>
import { Pin } from 'lucide-vue-next'

defineProps({
  compact: { type: Boolean, default: false }
})
</script>

<style scoped>
.pinned-badge {
  position: absolute;
  top: -6px;
  right: 40px;
  width: 22px;
  height: 22px;
  background: linear-gradient(135deg, #EAB308 0%, #CA8A04 100%);
  border: 2px solid #1F2937;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  z-index: 15;
  box-shadow: 0 2px 6px rgba(234, 179, 8, 0.4);
  animation: pin-pop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.pinned-badge--compact {
  top: -4px;
  right: -4px;
  width: 18px;
  height: 18px;
}

@keyframes pin-pop {
  0% { transform: scale(0); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
</style>

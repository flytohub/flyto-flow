<template>
  <button
    @click="$emit('toggle')"
    class="collapse-handle"
    :title="collapsed ? $t('common.expand') : $t('common.collapse')"
  >
    <div class="handle-inner">
      <ChevronRight
        :size="18"
        :class="['handle-icon', collapsed ? 'rotated' : '']"
      />
    </div>
  </button>
</template>

<script setup>
import { ChevronRight } from 'lucide-vue-next'

defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
})

defineEmits(['toggle'])
</script>

<style scoped>
.collapse-handle {
  position: absolute;
  left: -28px;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 56px;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  border: 1px solid #334155;
  border-right: none;
  border-radius: 8px 0 0 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  transition: all 0.2s;
}

.collapse-handle:hover {
  background: rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.4);
}

.handle-inner {
  display: flex;
  align-items: center;
  justify-content: center;
}

.handle-icon {
  color: #94a3b8;
  transition: transform 0.3s ease, color 0.2s;
}

.collapse-handle:hover .handle-icon {
  color: #A78BFA;
}

.handle-icon.rotated {
  transform: rotate(180deg);
}
</style>

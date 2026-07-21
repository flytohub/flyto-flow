<template>
  <div class="tool-header">
    <div class="tool-icon">
      <component :is="iconComponent" :size="32" />
    </div>
    <div class="tool-info">
      <h1 class="tool-title">{{ tool?.meta?.name || 'Tool' }}</h1>
      <p class="tool-desc">{{ tool?.meta?.description }}</p>
    </div>
    <button
      v-if="showAdvancedToggle"
      class="mode-toggle"
      @click="$emit('toggle-advanced')"
    >
      <Settings :size="16" />
      {{ $t('simpleToolView.advancedMode') }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Settings, Image, FileText, File } from 'lucide-vue-next'

const props = defineProps({
  tool: {
    type: Object,
    required: true
  },
  showAdvancedToggle: {
    type: Boolean,
    default: true
  }
})

defineEmits(['toggle-advanced'])

const iconComponent = computed(() => {
  const iconName = props.tool?.meta?.icon
  const iconMap = { Image, FileText, File }
  return iconMap[iconName] || File
})
</script>

<style scoped>
.tool-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #334155;
}

.tool-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  border-radius: 16px;
  color: white;
}

.tool-info {
  flex: 1;
}

.tool-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 4px;
  color: #f1f5f9;
}

.tool-desc {
  font-size: 14px;
  color: #94a3b8;
  margin: 0;
}

.mode-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid #475569;
  border-radius: 8px;
  background: transparent;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-toggle:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}
</style>

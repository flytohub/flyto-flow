<template>
  <div class="component-grid">
    <button
      v-for="comp in components"
      :key="comp.type"
      @click="$emit('add-component', comp.type)"
      class="component-card"
      :title="$t('templateBuilder.componentToolbox.addComponent', { component: comp.label })"
    >
      <div class="component-icon" :style="{ '--comp-color': getComponentColor(comp.type) }">
        <component :is="comp.icon" :size="20" />
      </div>
      <span class="component-label">{{ comp.label }}</span>
    </button>
  </div>
</template>

<script setup>
import { getComponentColor } from '../../_config/colorPalette'

defineProps({
  components: {
    type: Array,
    required: true
  }
})

defineEmits(['add-component'])
</script>

<style scoped>
.component-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.component-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 14px 10px;
  border-radius: 12px;
  border: 1px solid #334155;
  background: rgba(30, 41, 59, 0.5);
  cursor: pointer;
  transition: all 0.2s;
}

.component-card:hover {
  border-color: #8B5CF6;
  background: rgba(139, 92, 246, 0.1);
  transform: translateY(-2px);
}

.component-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--comp-color) 15%, transparent);
  border: 1px solid color-mix(in srgb, var(--comp-color) 30%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--comp-color);
}

.component-label {
  font-size: 11px;
  font-weight: 500;
  color: #94a3b8;
  text-align: center;
}
</style>

<template>
  <div class="toolbox-header">
    <div class="header-icon">
      <Blocks :size="18" />
    </div>
    <div class="header-text">
      <h3>{{ $t('templateBuilder.componentToolbox.title') }}</h3>
      <p>{{ subtitle }}</p>
    </div>
  </div>
</template>

<script setup>
import { Blocks } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import { computed } from 'vue'

const { t } = useI18n()

const props = defineProps({
  selectedSection: {
    type: Number,
    default: null
  },
  selectedColumn: {
    type: Number,
    default: null
  }
})

const subtitle = computed(() => {
  if (props.selectedSection !== null && props.selectedColumn !== null) {
    return t('templateBuilder.componentToolbox.selectColumnHint', { column: props.selectedColumn + 1 })
  }
  return t('templateBuilder.componentToolbox.selectColumnFirst')
})
</script>

<style scoped>
.toolbox-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px;
  border-bottom: 1px solid #334155;
}

.header-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.header-text h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #f1f5f9;
}

.header-text p {
  margin: 4px 0 0;
  font-size: 11px;
  color: #94a3b8;
}
</style>

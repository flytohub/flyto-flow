<template>
  <div v-if="hasActiveFilters" class="filter-chips" role="region" :aria-label="t('common.activeFilters')">
    <span class="filter-label">{{ t('common.filters') }}:</span>
    <div class="chips-container">
      <button
        v-for="filter in activeFilters"
        :key="filter.key"
        type="button"
        class="filter-chip"
        :aria-label="`${t('common.remove')} ${filter.label}`"
        @click="removeFilter(filter.key)"
      >
        <span class="chip-label">{{ filter.label }}</span>
        <X :size="14" aria-hidden="true" />
      </button>
    </div>
    <button
      v-if="activeFilters.length > 1"
      type="button"
      class="clear-all-btn"
      @click="clearAll"
    >
      {{ t('common.clearAll') }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { X } from 'lucide-vue-next'

const props = defineProps({
  filters: {
    type: Object,
    required: true
  },
  labels: {
    type: Object,
    default: () => ({})
  },
  exclude: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['remove', 'clear'])

const { t } = useI18n()

const activeFilters = computed(() => {
  const result = []
  for (const [key, value] of Object.entries(props.filters)) {
    if (props.exclude.includes(key)) continue
    if (value === null || value === undefined || value === '' || value === 'all') continue
    if (Array.isArray(value) && value.length === 0) continue

    const label = props.labels[key]
      ? `${props.labels[key]}: ${formatValue(value)}`
      : formatValue(value)

    result.push({ key, value, label })
  }
  return result
})

const hasActiveFilters = computed(() => activeFilters.value.length > 0)

function formatValue(value) {
  if (Array.isArray(value)) {
    return value.join(', ')
  }
  if (typeof value === 'boolean') {
    return value ? t('common.yes') : t('common.no')
  }
  return String(value)
}

function removeFilter(key) {
  emit('remove', key)
}

function clearAll() {
  emit('clear')
}
</script>

<style scoped>
.filter-chips {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  padding: 0.75rem 1rem;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 0.5rem;
  border: 1px solid rgba(139, 92, 246, 0.2);
}

.filter-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #8b5cf6;
  flex-shrink: 0;
}

.chips-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  flex: 1;
}

.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.625rem;
  background: rgba(139, 92, 246, 0.2);
  border: none;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
  color: #a78bfa;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-chip:hover {
  background: rgba(139, 92, 246, 0.3);
  color: #c4b5fd;
}

.filter-chip:focus-visible {
  outline: 2px solid #8b5cf6;
  outline-offset: 2px;
}

.chip-label {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.clear-all-btn {
  padding: 0.375rem 0.75rem;
  background: transparent;
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: #8b5cf6;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.clear-all-btn:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.5);
}

.clear-all-btn:focus-visible {
  outline: 2px solid #8b5cf6;
  outline-offset: 2px;
}

/* Dark mode support */
.dark .filter-chips {
  background: rgba(139, 92, 246, 0.05);
  border-color: rgba(139, 92, 246, 0.15);
}
</style>

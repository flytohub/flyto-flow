<template>
  <div class="execution-filters">
    <!-- Search Box -->
    <div class="filter-group search-group">
      <div class="search-input-wrapper">
        <Search :size="16" class="search-icon" />
        <AppInput
          v-model="searchQuery"
          :placeholder="$t('executionHistory.searchPlaceholder')"
          @input="debouncedEmit"
        />
        <button
          v-if="searchQuery"
          @click="clearSearch"
          class="clear-btn"
          aria-label="Clear search"
        >
          <X :size="14" />
        </button>
      </div>
    </div>

    <!-- Status Filter -->
    <div class="filter-group">
      <label class="filter-label">{{ $t('executionHistory.status') }}</label>
      <div class="status-chips">
        <button
          v-for="status in statusOptions"
          :key="status.value"
          @click="toggleStatus(status.value)"
          class="status-chip"
          :class="{ active: selectedStatuses.includes(status.value) }"
          :style="{ '--chip-color': status.color }"
          :aria-label="status.label"
        >
          <component :is="status.icon" :size="12" />
          {{ status.label }}
        </button>
      </div>
    </div>

    <!-- Time Range -->
    <div class="filter-group">
      <label class="filter-label">{{ $t('executionHistory.timeRange') }}</label>
      <div class="time-range-row">
        <!-- Quick Presets -->
        <div class="time-presets">
          <button
            v-for="preset in timePresets"
            :key="preset.value"
            @click="selectTimePreset(preset.value)"
            class="time-preset-btn"
            :class="{ active: selectedTimePreset === preset.value }"
            :aria-label="preset.label"
          >
            {{ preset.label }}
          </button>
        </div>

        <!-- Custom Date Range -->
        <div class="custom-range">
          <input
            v-model="startDate"
            type="datetime-local"
            class="date-input"
            :max="endDate || undefined"
            @change="handleCustomRange"
          />
          <span class="date-separator">{{ $t('executionHistory.to') }}</span>
          <input
            v-model="endDate"
            type="datetime-local"
            class="date-input"
            :min="startDate || undefined"
            @change="handleCustomRange"
          />
        </div>
      </div>
    </div>

    <!-- Results Summary & Actions -->
    <div class="filter-actions">
      <span class="results-count">
        {{ $t('executionHistory.resultsCount', { count: resultCount }) }}
      </span>
      <button
        v-if="hasActiveFilters"
        @click="clearAllFilters"
        class="clear-all-btn"
        aria-label="Clear filters"
      >
        <RotateCcw :size="14" />
        {{ $t('executionHistory.clearFilters') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Search,
  X,
  RotateCcw,
  CheckCircle,
  XCircle,
  Loader,
  Clock,
  Pause
} from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'

const props = defineProps({
  resultCount: {
    type: Number,
    default: 0
  },
  initialFilters: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['filter-change'])
const { t } = useI18n()

// Search state
const searchQuery = ref(props.initialFilters.search || '')

// Status filter state
const selectedStatuses = ref(props.initialFilters.statuses || [])

const statusOptions = [
  { value: 'success', label: t('executionHistory.statusSuccess'), icon: CheckCircle, color: '#22c55e' },
  { value: 'failed', label: t('executionHistory.statusFailed'), icon: XCircle, color: '#ef4444' },
  { value: 'running', label: t('executionHistory.statusRunning'), icon: Loader, color: '#3b82f6' },
  { value: 'pending', label: t('executionHistory.statusPending'), icon: Clock, color: '#a855f7' },
  { value: 'paused', label: t('executionHistory.statusPaused'), icon: Pause, color: '#f59e0b' }
]

// Time range state
const selectedTimePreset = ref(props.initialFilters.timePreset || 'all')
const startDate = ref(props.initialFilters.startDate || '')
const endDate = ref(props.initialFilters.endDate || '')

const timePresets = [
  { value: 'all', label: t('executionHistory.timeAll') },
  { value: '1h', label: t('executionHistory.time1h') },
  { value: '24h', label: t('executionHistory.time24h') },
  { value: '7d', label: t('executionHistory.time7d') },
  { value: '30d', label: t('executionHistory.time30d') },
  { value: 'custom', label: t('executionHistory.timeCustom') }
]

// Computed
const hasActiveFilters = computed(() => {
  return searchQuery.value ||
    selectedStatuses.value.length > 0 ||
    selectedTimePreset.value !== 'all'
})

const currentFilters = computed(() => ({
  search: searchQuery.value,
  statuses: selectedStatuses.value,
  timePreset: selectedTimePreset.value,
  startDate: startDate.value,
  endDate: endDate.value,
  // Computed date range based on preset
  dateRange: getDateRange()
}))

// Methods
function getDateRange() {
  if (selectedTimePreset.value === 'custom') {
    return {
      start: startDate.value ? new Date(startDate.value).toISOString() : null,
      end: endDate.value ? new Date(endDate.value).toISOString() : null
    }
  }

  if (selectedTimePreset.value === 'all') {
    return { start: null, end: null }
  }

  const now = new Date()
  const ranges = {
    '1h': 60 * 60 * 1000,
    '24h': 24 * 60 * 60 * 1000,
    '7d': 7 * 24 * 60 * 60 * 1000,
    '30d': 30 * 24 * 60 * 60 * 1000
  }

  const ms = ranges[selectedTimePreset.value]
  if (!ms) return { start: null, end: null }

  return {
    start: new Date(now.getTime() - ms).toISOString(),
    end: now.toISOString()
  }
}

function toggleStatus(status) {
  const idx = selectedStatuses.value.indexOf(status)
  if (idx === -1) {
    selectedStatuses.value.push(status)
  } else {
    selectedStatuses.value.splice(idx, 1)
  }
  emitFilters()
}

function selectTimePreset(preset) {
  selectedTimePreset.value = preset
  if (preset !== 'custom') {
    startDate.value = ''
    endDate.value = ''
  }
  emitFilters()
}

function handleCustomRange() {
  selectedTimePreset.value = 'custom'
  emitFilters()
}

function clearSearch() {
  searchQuery.value = ''
  emitFilters()
}

function clearAllFilters() {
  searchQuery.value = ''
  selectedStatuses.value = []
  selectedTimePreset.value = 'all'
  startDate.value = ''
  endDate.value = ''
  emitFilters()
}

// Debounced emit for search input
let debounceTimer = null
function debouncedEmit() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    emitFilters()
  }, 300)
}

function emitFilters() {
  emit('filter-change', currentFilters.value)
}

// Initial emit
emitFilters()
</script>

<style scoped>
.execution-filters {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 12px;
}

/* Filter Group */
.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #64748b;
}

/* Search */
.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: #64748b;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 10px 36px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 8px;
  color: #f1f5f9;
  font-size: 13px;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #8B5CF6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.search-input::placeholder {
  color: #475569;
}

.clear-btn {
  position: absolute;
  right: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: rgba(71, 85, 105, 0.4);
  border: none;
  border-radius: 6px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: rgba(239, 68, 68, 0.3);
  color: #f87171;
}

/* Status Chips */
.status-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.status-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(71, 85, 105, 0.2);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 20px;
  color: #94a3b8;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.status-chip:hover {
  background: rgba(71, 85, 105, 0.4);
  border-color: rgba(71, 85, 105, 0.6);
  color: #e2e8f0;
}

.status-chip.active {
  background: color-mix(in srgb, var(--chip-color) 20%, transparent);
  border-color: var(--chip-color);
  color: var(--chip-color);
}

/* Time Range */
.time-range-row {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.time-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.time-preset-btn {
  padding: 6px 12px;
  background: rgba(71, 85, 105, 0.2);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 6px;
  color: #94a3b8;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.time-preset-btn:hover {
  background: rgba(71, 85, 105, 0.4);
  border-color: rgba(71, 85, 105, 0.6);
  color: #e2e8f0;
}

.time-preset-btn.active {
  background: rgba(139, 92, 246, 0.2);
  border-color: #8B5CF6;
  color: #a78bfa;
}

.custom-range {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-input {
  flex: 1;
  padding: 8px 12px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 8px;
  color: #f1f5f9;
  font-size: 12px;
  transition: all 0.2s;
}

.date-input:focus {
  outline: none;
  border-color: #8B5CF6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.date-separator {
  color: #64748b;
  font-size: 12px;
}

/* Filter Actions */
.filter-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid rgba(71, 85, 105, 0.3);
}

.results-count {
  font-size: 12px;
  color: #64748b;
}

.clear-all-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: transparent;
  border: 1px solid rgba(239, 68, 68, 0.4);
  border-radius: 6px;
  color: #f87171;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-all-btn:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.6);
}

/* Responsive */
@media (max-width: 640px) {
  .custom-range {
    flex-direction: column;
    align-items: stretch;
  }

  .date-separator {
    text-align: center;
  }
}
</style>

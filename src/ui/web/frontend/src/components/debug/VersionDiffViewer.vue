<template>
  <div class="version-diff-viewer">
    <!-- Header -->
    <div class="diff-header">
      <div class="diff-title">
        <GitCompare :size="18" class="diff-icon" />
        <span>{{ $t('versionDiff.title') }}</span>
      </div>
      <button @click="$emit('close')" class="close-btn" aria-label="Close">
        <X :size="18" />
      </button>
    </div>

    <!-- Version Selectors -->
    <div class="version-selectors">
      <div class="version-select-group">
        <label>{{ $t('versionDiff.from') }}</label>
        <AppSelect
          v-model="fromVersion"
          :options="versions.map(v => ({ value: v.version, label: 'v' + v.version + (v.version === currentVersion ? ` (${$t('versionDiff.current')})` : '') }))"
        />
      </div>
      <ArrowRight :size="18" class="arrow-icon" />
      <div class="version-select-group">
        <label>{{ $t('versionDiff.to') }}</label>
        <AppSelect
          v-model="toVersion"
          :options="versions.map(v => ({ value: v.version, label: 'v' + v.version + (v.version === currentVersion ? ` (${$t('versionDiff.current')})` : '') }))"
        />
      </div>
      <button @click="computeDiff" class="compare-btn" :disabled="!canCompare" aria-label="Compare versions">
        <GitCompare :size="16" />
        {{ $t('versionDiff.compare') }}
      </button>
    </div>

    <!-- Diff Loading -->
    <div v-if="isLoading" class="diff-loading">
      <Loader :size="24" class="loading-spinner" />
      <span>{{ $t('versionDiff.computing') }}</span>
    </div>

    <!-- No Diff State -->
    <div v-else-if="!diffResult" class="diff-empty">
      <GitCompare :size="32" class="empty-icon" />
      <p>{{ $t('versionDiff.selectVersions') }}</p>
    </div>

    <!-- Same Version -->
    <div v-else-if="diffResult.identical" class="diff-identical">
      <Check :size="24" class="identical-icon" />
      <p>{{ $t('versionDiff.noChanges') }}</p>
    </div>

    <!-- Diff Content -->
    <div v-else class="diff-content">
      <!-- Summary -->
      <div class="diff-summary">
        <div class="summary-stat added">
          <Plus :size="14" />
          <span>{{ diffResult.stats.added }} {{ $t('versionDiff.added') }}</span>
        </div>
        <div class="summary-stat removed">
          <Minus :size="14" />
          <span>{{ diffResult.stats.removed }} {{ $t('versionDiff.removed') }}</span>
        </div>
        <div class="summary-stat modified">
          <RefreshCw :size="14" />
          <span>{{ diffResult.stats.modified }} {{ $t('versionDiff.modified') }}</span>
        </div>
      </div>

      <!-- Changes List -->
      <div class="diff-changes">
        <!-- Added Items -->
        <div v-if="diffResult.added.length" class="change-section">
          <div class="section-header added">
            <Plus :size="14" />
            {{ $t('versionDiff.addedItems') }} ({{ diffResult.added.length }})
          </div>
          <div v-for="item in diffResult.added" :key="item.path" class="change-item added">
            <span class="change-path">{{ item.path }}</span>
            <pre class="change-value">{{ formatValue(item.value) }}</pre>
          </div>
        </div>

        <!-- Removed Items -->
        <div v-if="diffResult.removed.length" class="change-section">
          <div class="section-header removed">
            <Minus :size="14" />
            {{ $t('versionDiff.removedItems') }} ({{ diffResult.removed.length }})
          </div>
          <div v-for="item in diffResult.removed" :key="item.path" class="change-item removed">
            <span class="change-path">{{ item.path }}</span>
            <pre class="change-value">{{ formatValue(item.value) }}</pre>
          </div>
        </div>

        <!-- Modified Items -->
        <div v-if="diffResult.modified.length" class="change-section">
          <div class="section-header modified">
            <RefreshCw :size="14" />
            {{ $t('versionDiff.modifiedItems') }} ({{ diffResult.modified.length }})
          </div>
          <div v-for="item in diffResult.modified" :key="item.path" class="change-item modified">
            <span class="change-path">{{ item.path }}</span>
            <div class="change-comparison">
              <div class="old-value">
                <span class="value-label">{{ $t('versionDiff.old') }}</span>
                <pre>{{ formatValue(item.oldValue) }}</pre>
              </div>
              <ArrowRight :size="14" class="change-arrow" />
              <div class="new-value">
                <span class="value-label">{{ $t('versionDiff.new') }}</span>
                <pre>{{ formatValue(item.newValue) }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import AppSelect from '@/components/common/AppSelect.vue'
import {
  GitCompare,
  X,
  ArrowRight,
  Loader,
  Check,
  Plus,
  Minus,
  RefreshCw
} from 'lucide-vue-next'

const props = defineProps({
  versions: {
    type: Array,
    required: true
  },
  currentVersion: {
    type: String,
    default: ''
  },
  getVersionData: {
    type: Function,
    required: true
    // Should return Promise<Object> with version data
  }
})

const emit = defineEmits(['close'])

// State
const fromVersion = ref(props.versions[1]?.version || '')
const toVersion = ref(props.versions[0]?.version || '')
const isLoading = ref(false)
const diffResult = ref(null)

// Computed
const canCompare = computed(() =>
  fromVersion.value &&
  toVersion.value &&
  fromVersion.value !== toVersion.value
)

// Methods
async function computeDiff() {
  if (!canCompare.value) return

  isLoading.value = true
  diffResult.value = null

  try {
    // Get data for both versions
    const [fromData, toData] = await Promise.all([
      props.getVersionData(fromVersion.value),
      props.getVersionData(toVersion.value)
    ])

    // Compute diff
    diffResult.value = computeObjectDiff(fromData, toData)
  } catch (error) {
    console.error('[VersionDiffViewer] Failed to compute diff:', error)
    diffResult.value = null
  } finally {
    isLoading.value = false
  }
}

/**
 * Compute differences between two objects
 */
function computeObjectDiff(oldObj, newObj, path = '') {
  const added = []
  const removed = []
  const modified = []

  // Flatten both objects
  const oldFlat = flattenObject(oldObj)
  const newFlat = flattenObject(newObj)

  const allKeys = new Set([...Object.keys(oldFlat), ...Object.keys(newFlat)])

  for (const key of allKeys) {
    const oldVal = oldFlat[key]
    const newVal = newFlat[key]

    if (oldVal === undefined && newVal !== undefined) {
      added.push({ path: key, value: newVal })
    } else if (oldVal !== undefined && newVal === undefined) {
      removed.push({ path: key, value: oldVal })
    } else if (JSON.stringify(oldVal) !== JSON.stringify(newVal)) {
      modified.push({ path: key, oldValue: oldVal, newValue: newVal })
    }
  }

  const identical = added.length === 0 && removed.length === 0 && modified.length === 0

  return {
    identical,
    added,
    removed,
    modified,
    stats: {
      added: added.length,
      removed: removed.length,
      modified: modified.length
    }
  }
}

/**
 * Flatten a nested object to dot-notation paths
 */
function flattenObject(obj, prefix = '') {
  const result = {}

  if (obj === null || obj === undefined) {
    return result
  }

  if (typeof obj !== 'object') {
    return { [prefix || 'value']: obj }
  }

  if (Array.isArray(obj)) {
    obj.forEach((item, i) => {
      const key = prefix ? `${prefix}[${i}]` : `[${i}]`
      if (typeof item === 'object' && item !== null) {
        Object.assign(result, flattenObject(item, key))
      } else {
        result[key] = item
      }
    })
    return result
  }

  for (const key of Object.keys(obj)) {
    const val = obj[key]
    const newKey = prefix ? `${prefix}.${key}` : key

    if (typeof val === 'object' && val !== null && !Array.isArray(val)) {
      Object.assign(result, flattenObject(val, newKey))
    } else if (Array.isArray(val)) {
      Object.assign(result, flattenObject(val, newKey))
    } else {
      result[newKey] = val
    }
  }

  return result
}

/**
 * Format a value for display
 */
function formatValue(value) {
  if (value === null) return 'null'
  if (value === undefined) return 'undefined'
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value, null, 2)
    } catch {
      return String(value)
    }
  }
  if (typeof value === 'string') return `"${value}"`
  return String(value)
}

// Auto-select versions on mount
watch(() => props.versions, (versions) => {
  if (versions.length >= 2) {
    fromVersion.value = versions[1].version
    toVersion.value = versions[0].version
  }
}, { immediate: true })
</script>

<style scoped>
.version-diff-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #0f172a;
}

/* Header */
.diff-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.4);
  background: rgba(30, 41, 59, 0.6);
}

.diff-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
}

.diff-icon {
  color: #8B5CF6;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

/* Version Selectors */
.version-selectors {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.4);
}

.version-select-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.version-select-group label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #64748b;
}

.arrow-icon {
  color: #64748b;
  margin-bottom: 8px;
}

.compare-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.compare-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

.compare-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Loading & Empty States */
.diff-loading,
.diff-empty,
.diff-identical {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 12px;
  color: #64748b;
}

.loading-spinner {
  color: #8B5CF6;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-icon {
  opacity: 0.4;
}

.identical-icon {
  color: #22c55e;
}

/* Diff Content */
.diff-content {
  flex: 1;
  overflow: auto;
}

/* Summary */
.diff-summary {
  display: flex;
  gap: 16px;
  padding: 12px 16px;
  background: rgba(30, 41, 59, 0.6);
  border-bottom: 1px solid rgba(71, 85, 105, 0.4);
}

.summary-stat {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
}

.summary-stat.added { color: #22c55e; }
.summary-stat.removed { color: #ef4444; }
.summary-stat.modified { color: #f59e0b; }

/* Changes */
.diff-changes {
  padding: 16px;
}

.change-section {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px 8px 0 0;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.section-header.added {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.section-header.removed {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.section-header.modified {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.change-item {
  padding: 12px;
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-top: none;
  background: rgba(15, 23, 42, 0.6);
}

.change-item:last-child {
  border-radius: 0 0 8px 8px;
}

.change-path {
  display: block;
  font-family: 'SF Mono', Monaco, 'Fira Code', monospace;
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 8px;
}

.change-value {
  margin: 0;
  padding: 8px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
  font-family: 'SF Mono', Monaco, 'Fira Code', monospace;
  font-size: 11px;
  color: #e2e8f0;
  white-space: pre-wrap;
  word-break: break-word;
}

.change-item.added .change-value {
  border-left: 3px solid #22c55e;
}

.change-item.removed .change-value {
  border-left: 3px solid #ef4444;
}

/* Modified Item */
.change-comparison {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.old-value,
.new-value {
  flex: 1;
  min-width: 0;
}

.value-label {
  display: block;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.old-value .value-label { color: #ef4444; }
.new-value .value-label { color: #22c55e; }

.old-value pre,
.new-value pre {
  margin: 0;
  padding: 8px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
  font-family: 'SF Mono', Monaco, 'Fira Code', monospace;
  font-size: 11px;
  color: #e2e8f0;
  white-space: pre-wrap;
  word-break: break-word;
}

.old-value pre { border-left: 3px solid #ef4444; }
.new-value pre { border-left: 3px solid #22c55e; }

.change-arrow {
  color: #64748b;
  flex-shrink: 0;
  margin-top: 24px;
}

/* Scrollbar */
.diff-content::-webkit-scrollbar {
  width: 6px;
}

.diff-content::-webkit-scrollbar-track {
  background: transparent;
}

.diff-content::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.4);
  border-radius: 3px;
}
</style>

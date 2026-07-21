<template>
  <div class="output-section">
    <div class="section-label">
      <Download :size="18" />
      <span>{{ $t('simpleToolView.output') }}</span>
    </div>

    <div class="output-area" :class="{ 'has-result': hasResult, 'has-error': hasError }">
      <!-- Empty State -->
      <div v-if="!hasResult && !hasError && !isExecuting" class="output-empty">
        <Monitor :size="48" />
        <span>{{ $t('simpleToolView.resultWillAppear') }}</span>
      </div>

      <!-- Loading State -->
      <div v-else-if="isExecuting" class="output-loading">
        <Loader :size="32" class="spin" />
        <span>{{ $t('simpleToolView.generating') }}</span>
      </div>

      <!-- Error State -->
      <div v-else-if="hasError" class="output-error">
        <AlertCircle :size="32" />
        <span class="error-title">{{ $t('simpleToolView.failed') }}</span>
        <span class="error-message">{{ errorMessage }}</span>
        <button class="retry-btn" @click="$emit('retry')">
          <RotateCcw :size="14" />
          {{ $t('simpleToolView.retry') }}
        </button>
      </div>

      <!-- Success: Image Result -->
      <div v-else-if="resultType === 'image'" class="output-image">
        <img :src="resultImageUrl" :alt="$t('alt.result')" />
        <div class="output-actions">
          <button class="action-btn primary" @click="$emit('download')">
            <Download :size="16" />
            {{ $t('simpleToolView.download') }}
          </button>
          <button class="action-btn" @click="$emit('copy-image')">
            <Copy :size="16" />
          </button>
        </div>
      </div>

      <!-- Success: File Result -->
      <div v-else-if="resultType === 'file'" class="output-file">
        <div class="file-result-card">
          <FileDown :size="40" />
          <div class="file-info">
            <span class="file-name">{{ resultFileName }}</span>
            <span class="file-size">{{ resultFileSize }}</span>
          </div>
        </div>
        <button class="action-btn primary full" @click="$emit('download')">
          <Download :size="16" />
          {{ $t('simpleToolView.downloadFile') }}
        </button>
      </div>

      <!-- Success: Text/JSON Result -->
      <div v-else-if="resultType === 'text' || resultType === 'json'" class="output-text">
        <pre class="result-content">{{ formattedResult }}</pre>
        <div class="output-actions">
          <button class="action-btn primary" @click="$emit('copy')">
            <Copy :size="16" />
            {{ $t('simpleToolView.copy') }}
          </button>
          <button class="action-btn" @click="$emit('download-as-file')">
            <Download :size="16" />
          </button>
        </div>
      </div>

      <!-- Success: Table Result -->
      <div v-else-if="resultType === 'table'" class="output-table">
        <table>
          <thead>
            <tr>
              <th v-for="col in tableColumns" :key="col">{{ col }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in tableRows.slice(0, 10)" :key="idx">
              <td v-for="col in tableColumns" :key="col">{{ row[col] }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="tableRows.length > 10" class="table-more">
          {{ $t('simpleToolView.moreRows', { count: tableRows.length - 10 }) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  Download, Monitor, Loader, AlertCircle, RotateCcw,
  Copy, FileDown
} from 'lucide-vue-next'

const props = defineProps({
  isExecuting: {
    type: Boolean,
    default: false
  },
  executionResult: {
    type: [Object, Array, String],
    default: null
  },
  errorMessage: {
    type: String,
    default: null
  }
})

defineEmits(['retry', 'download', 'copy', 'copy-image', 'download-as-file'])

const hasResult = computed(() => props.executionResult !== null)
const hasError = computed(() => props.errorMessage !== null)

const resultType = computed(() => {
  const result = props.executionResult
  if (!result) return null

  if (result.image || result.imageUrl || result.image_url || result.imageBase64 || result.image_base64) return 'image'
  if (result.file || result.fileUrl || result.file_url || result.downloadUrl || result.download_url) return 'file'
  if (Array.isArray(result) || Array.isArray(result.data) || Array.isArray(result.rows)) return 'table'
  if (typeof result === 'string') return 'text'
  return 'json'
})

const resultImageUrl = computed(() => {
  const r = props.executionResult
  if (r?.imageBase64 || r?.image_base64) return `data:image/png;base64,${r.imageBase64 || r.image_base64}`
  return r?.imageUrl || r?.image_url || r?.image || null
})

const resultFileName = computed(() => {
  const r = props.executionResult
  return r?.filename || r?.name || 'output'
})

const resultFileSize = computed(() => {
  const r = props.executionResult
  if (!r?.size) return ''
  const bytes = r.size
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
})

const formattedResult = computed(() => {
  const r = props.executionResult
  if (typeof r === 'string') return r
  return JSON.stringify(r, null, 2)
})

const tableColumns = computed(() => {
  const data = props.executionResult?.data || props.executionResult?.rows || props.executionResult
  if (!Array.isArray(data) || data.length === 0) return []
  return Object.keys(data[0])
})

const tableRows = computed(() => {
  return props.executionResult?.data || props.executionResult?.rows || props.executionResult || []
})
</script>

<style scoped>
.output-section {
  min-height: 300px;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 16px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.output-area {
  min-height: 250px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.output-area.has-result {
  border-color: #10b981;
}

.output-area.has-error {
  border-color: #ef4444;
}

.output-empty,
.output-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #64748b;
  padding: 40px;
  text-align: center;
}

.output-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
  color: #ef4444;
  text-align: center;
}

.error-title {
  font-weight: 600;
}

.error-message {
  font-size: 13px;
  color: #fca5a5;
}

.retry-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid #ef4444;
  border-radius: 6px;
  background: transparent;
  color: #ef4444;
  font-size: 13px;
  cursor: pointer;
  margin-top: 8px;
}

.output-image {
  width: 100%;
  padding: 16px;
}

.output-image img {
  width: 100%;
  max-height: 300px;
  object-fit: contain;
  border-radius: 8px;
}

.output-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  justify-content: center;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border: 1px solid #334155;
  border-radius: 8px;
  background: transparent;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  border-color: #475569;
  color: #f1f5f9;
}

.action-btn.primary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  border: none;
  color: white;
}

.action-btn.primary:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
}

.action-btn.full {
  width: 100%;
  justify-content: center;
}

.output-file {
  width: 100%;
  padding: 24px;
}

.file-result-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #0f172a;
  border-radius: 8px;
  margin-bottom: 16px;
  color: #64748b;
}

.file-result-card .file-info {
  flex: 1;
}

.file-result-card .file-name {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #f1f5f9;
}

.file-result-card .file-size {
  font-size: 12px;
}

.output-text {
  width: 100%;
  padding: 16px;
}

.result-content {
  background: #0f172a;
  border-radius: 8px;
  padding: 16px;
  margin: 0;
  max-height: 200px;
  overflow: auto;
  font-family: 'Fira Code', monospace;
  font-size: 12px;
  color: #94a3b8;
}

.output-table {
  width: 100%;
  padding: 16px;
  overflow-x: auto;
}

.output-table table {
  width: 100%;
  border-collapse: collapse;
}

.output-table th,
.output-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #334155;
  font-size: 13px;
}

.output-table th {
  background: #0f172a;
  font-weight: 500;
  color: #94a3b8;
}

.table-more {
  text-align: center;
  padding: 12px;
  font-size: 12px;
  color: #64748b;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>

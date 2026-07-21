<template>
  <div class="results-panel">
    <div class="panel-header">
      <Eye :size="18" />
      <span>{{ $t('toolRunner.results') }}</span>
    </div>

    <div class="results-content">
      <!-- No result yet -->
      <div v-if="!result && !error" class="no-result">
        <Monitor :size="48" />
        <span>{{ $t('toolRunner.runToSeeResults') }}</span>
      </div>

      <!-- Error result -->
      <div v-else-if="error" class="error-result">
        <div class="error-header">
          <AlertCircle :size="20" />
          <span>{{ $t('toolRunner.executionFailed') }}</span>
        </div>
        <div class="error-message">{{ error }}</div>
        <button class="retry-btn" @click="$emit('retry')">
          <RotateCcw :size="14" />
          {{ $t('toolRunner.retry') }}
        </button>
      </div>

      <!-- Success result -->
      <div v-else class="success-result">
        <div class="result-header">
          <CheckCircle :size="20" class="success-icon" />
          <span>{{ $t('toolRunner.executionSuccess') }}</span>
        </div>

        <!-- Result display -->
        <div class="result-display">
          <!-- Image result -->
          <div v-if="resultType === 'image'" class="result-image">
            <img :src="resultData" :alt="$t('alt.result')" />
          </div>

          <!-- File result -->
          <div v-else-if="resultType === 'file'" class="result-file">
            <FileDown :size="24" />
            <span>{{ resultData?.name || 'output' }}</span>
            <button class="download-btn" @click="$emit('download')">
              <Download :size="14" />
              {{ $t('toolRunner.download') }}
            </button>
          </div>

          <!-- JSON/Text result -->
          <div v-else class="result-json">
            <pre>{{ JSON.stringify(result, null, 2) }}</pre>
          </div>
        </div>

        <!-- Actions -->
        <div class="result-actions">
          <button class="action-btn" @click="$emit('copy')">
            <Copy :size="14" />
            {{ $t('toolRunner.copy') }}
          </button>
          <button class="action-btn" @click="$emit('reset')">
            <RotateCcw :size="14" />
            {{ $t('toolRunner.runAgain') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  Eye, Monitor, AlertCircle, RotateCcw, CheckCircle,
  FileDown, Download, Copy
} from 'lucide-vue-next'

const props = defineProps({
  result: {
    type: [Object, String, Array],
    default: null
  },
  error: {
    type: String,
    default: null
  }
})

defineEmits(['retry', 'download', 'copy', 'reset'])

const resultType = computed(() => {
  if (!props.result) return null
  const r = props.result
  if (r.image || r.imageUrl || r.image_url || r.imageBase64 || r.image_base64) return 'image'
  if (r.file || r.fileUrl || r.file_url || r.downloadUrl || r.download_url) return 'file'
  return 'json'
})

const resultData = computed(() => {
  if (!props.result) return null
  const r = props.result
  if (r.imageBase64 || r.image_base64) return `data:image/png;base64,${r.imageBase64 || r.image_base64}`
  if (r.imageUrl || r.image_url || r.image) return r.imageUrl || r.image_url || r.image
  if (r.fileUrl || r.file_url || r.downloadUrl || r.download_url) {
    return { url: r.fileUrl || r.file_url || r.downloadUrl || r.download_url, name: r.filename || 'output' }
  }
  return r
})
</script>

<style scoped>
.results-panel {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 16px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  background: rgba(51, 65, 85, 0.5);
  border-bottom: 1px solid #334155;
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
}

.results-content {
  padding: 20px;
  min-height: 300px;
}

.no-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 20px;
  color: #64748b;
  text-align: center;
}

.error-result {
  padding: 20px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 12px;
}

.error-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ef4444;
  font-weight: 500;
  margin-bottom: 12px;
}

.error-message {
  font-size: 13px;
  color: #fca5a5;
  margin-bottom: 16px;
}

.retry-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid #ef4444;
  border-radius: 8px;
  background: transparent;
  color: #ef4444;
  font-size: 13px;
  cursor: pointer;
}

.success-result {
  padding: 16px;
  background: rgba(16, 185, 129, 0.05);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 12px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  color: #f1f5f9;
}

.success-icon {
  color: #10b981;
}

.result-display {
  margin-bottom: 16px;
}

.result-image img {
  max-width: 100%;
  border-radius: 8px;
}

.result-file {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #0f172a;
  border-radius: 8px;
  color: #64748b;
}

.result-file span {
  flex: 1;
  color: #f1f5f9;
}

.download-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: none;
  border-radius: 6px;
  background: #3b82f6;
  color: white;
  font-size: 13px;
  cursor: pointer;
}

.result-json {
  background: #0f172a;
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
}

.result-json pre {
  margin: 0;
  font-family: 'Fira Code', monospace;
  font-size: 12px;
  color: #94a3b8;
}

.result-actions {
  display: flex;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid rgba(16, 185, 129, 0.2);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid #334155;
  border-radius: 6px;
  background: transparent;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
}

.action-btn:hover {
  border-color: #475569;
  color: #f1f5f9;
}
</style>

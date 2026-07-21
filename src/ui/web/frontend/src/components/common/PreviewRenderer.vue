<template>
  <div class="preview-renderer">
    <!-- Loading State -->
    <div v-if="loading" class="preview-loading">
      <Loader2 :size="24" class="animate-spin" />
      <span>{{ $t('common.loading') }}</span>
    </div>

    <!-- Error State -->
    <div v-else-if="previewType === 'error' || error" class="preview-error">
      <AlertCircle :size="20" />
      <span>{{ errorMessage }}</span>
    </div>

    <!-- No Result -->
    <div v-else-if="previewType === 'none' || !result" class="preview-empty">
      <FileQuestion :size="24" />
      <span>{{ $t('moduleLab.noResult') }}</span>
    </div>

    <!-- Text Preview -->
    <div v-else-if="previewType === 'text'" class="preview-text">
      <div class="text-header">
        <button @click="copyText" class="copy-btn" :title="$t('common.copy')">
          <component :is="copied ? Check : Copy" :size="14" />
        </button>
      </div>
      <pre>{{ textContent }}</pre>
    </div>

    <!-- JSON Preview -->
    <div v-else-if="previewType === 'json'" class="preview-json">
      <div class="json-header">
        <span class="json-label">{{ $t('moduleLab.jsonLabel') }}</span>
        <button @click="copyJson" class="copy-btn" :title="$t('common.copy')">
          <component :is="copied ? Check : Copy" :size="14" />
        </button>
      </div>
      <pre><code>{{ formattedJson }}</code></pre>
    </div>

    <!-- Image Preview -->
    <div v-else-if="previewType === 'image'" class="preview-image">
      <img
        v-if="imageUrl"
        :src="imageUrl"
        :alt="$t('moduleLab.imagePreview')"
        @error="handleImageError"
      />
      <div v-else class="preview-empty">
        <ImageIcon :size="24" />
        <span>{{ $t('moduleLab.noImage') }}</span>
      </div>
    </div>

    <!-- File Preview -->
    <div v-else-if="previewType === 'file'" class="preview-file">
      <div v-for="(file, index) in fileList" :key="index" class="file-item">
        <FileIcon :size="18" />
        <span class="file-name">{{ getFileName(file) }}</span>
        <a
          v-if="file"
          :href="getFileUrl(file)"
          :download="getFileName(file)"
          class="download-btn"
        >
          <Download :size="14" />
        </a>
      </div>
    </div>

    <!-- Table Preview -->
    <div v-else-if="previewType === 'table'" class="preview-table">
      <table v-if="tableData.length > 0">
        <thead>
          <tr>
            <th v-for="col in tableColumns" :key="col">{{ col }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in tableData" :key="rowIndex">
            <td v-for="col in tableColumns" :key="col">{{ row[col] }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="preview-empty">
        <Table :size="24" />
        <span>{{ $t('moduleLab.noTableData') }}</span>
      </div>
    </div>

    <!-- PDF Preview -->
    <div v-else-if="previewType === 'pdf'" class="preview-pdf">
      <div class="pdf-placeholder">
        <FileText :size="32" />
        <span>{{ $t('moduleLab.pdfPreview') }}</span>
        <a v-if="pdfUrl" :href="pdfUrl" target="_blank" class="view-btn">
          <ExternalLink :size="14" />
          {{ $t('common.openInNewTab') }}
        </a>
      </div>
    </div>

    <!-- Fallback -->
    <div v-else class="preview-fallback">
      <pre>{{ JSON.stringify(result?.output, null, 2) }}</pre>
    </div>

    <!-- Execution Info -->
    <div v-if="result && showMeta" class="preview-meta">
      <span v-if="result.executionTime" class="meta-item">
        <Clock :size="12" />
        {{ result.executionTime }}ms
      </span>
      <span v-if="result.ok" class="meta-item success">
        <CheckCircle :size="12" />
        {{ $t('common.success') }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Loader2,
  AlertCircle,
  FileQuestion,
  Copy,
  Check,
  Download,
  FileIcon,
  ImageIcon,
  FileText,
  ExternalLink,
  Table,
  Clock,
  CheckCircle
} from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps({
  result: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: null
  },
  showMeta: {
    type: Boolean,
    default: true
  }
})

const copied = ref(false)

// Computed: Preview type
const previewType = computed(() => {
  if (props.error) return 'error'
  if (!props.result) return 'none'
  return props.result.previewType || 'json'
})

// Computed: Error message
const errorMessage = computed(() => {
  return props.error || props.result?.error || t('common.unknownError')
})

// Computed: Text content
const textContent = computed(() => {
  const output = props.result?.output
  if (typeof output === 'string') return output
  if (output?.text) return output.text
  if (output?.content) return output.content
  if (output?.message) return output.message
  return String(output)
})

// Computed: Formatted JSON
const formattedJson = computed(() => {
  try {
    const output = props.result?.output
    return JSON.stringify(output, null, 2)
  } catch {
    return String(props.result?.output)
  }
})

// Computed: Image URL
const imageUrl = computed(() => {
  const output = props.result?.output
  if (!output) return null
  return output.imageUrl || output.url || output.images?.[0] || output.filePath
})

// Computed: File list
const fileList = computed(() => {
  const output = props.result?.output
  if (!output) return []
  if (output.files) return output.files
  if (output.filePath) return [output.filePath]
  if (output.outputPath) return [output.outputPath]
  return []
})

// Computed: PDF URL
const pdfUrl = computed(() => {
  const output = props.result?.output
  if (!output) return null
  return output.pdfUrl || output.filePath || output.outputPath
})

// Computed: Table data
const tableData = computed(() => {
  const output = props.result?.output
  if (!Array.isArray(output)) return []
  return output.slice(0, 100) // Limit to 100 rows
})

// Computed: Table columns
const tableColumns = computed(() => {
  if (tableData.value.length === 0) return []
  const firstRow = tableData.value[0]
  if (typeof firstRow !== 'object') return []
  return Object.keys(firstRow)
})

// Actions
function getFileName(filePath) {
  if (!filePath) return 'file'
  return filePath.split('/').pop() || 'file'
}

function getFileUrl(filePath) {
  if (!filePath) return '#'
  if (filePath.startsWith('http')) return filePath
  return `/api/files/${encodeURIComponent(filePath)}`
}

function handleImageError(e) {
  e.target.src = 'data:image/svg+xml,...' // placeholder
}

async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    // Fallback for insecure contexts (HTTP, iframes)
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.cssText = 'position:fixed;left:-9999px'
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
  }
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

async function copyJson() {
  await copyToClipboard(formattedJson.value)
}

async function copyText() {
  await copyToClipboard(textContent.value)
}
</script>

<style scoped>
.preview-renderer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 8px;
  overflow: hidden;
}

/* States */
.preview-loading,
.preview-empty,
.preview-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
  color: #64748b;
  text-align: center;
}

.preview-error {
  color: #f87171;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Text Preview */
.preview-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.text-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 6px 12px;
  background: rgba(30, 41, 59, 0.8);
  border-bottom: 1px solid #334155;
}

.preview-text pre {
  flex: 1;
  overflow: auto;
  margin: 0;
  padding: 16px;
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #e2e8f0;
  white-space: pre-wrap;
  word-break: break-word;
}

/* JSON Preview */
.preview-json {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.json-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(30, 41, 59, 0.8);
  border-bottom: 1px solid #334155;
}

.json-label {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
}

.copy-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #e2e8f0;
}

.preview-json pre {
  flex: 1;
  margin: 0;
  padding: 16px;
  overflow: auto;
}

.preview-json code {
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #a78bfa;
}

/* Image Preview */
.preview-image {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  overflow: auto;
}

.preview-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 8px;
}

/* File Preview */
.preview-file {
  flex: 1;
  padding: 16px;
  overflow: auto;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid #334155;
  border-radius: 8px;
  margin-bottom: 8px;
  color: #e2e8f0;
}

.file-name {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.download-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  transition: all 0.2s;
}

.download-btn:hover {
  background: rgba(16, 185, 129, 0.25);
}

/* Table Preview */
.preview-table {
  flex: 1;
  overflow: auto;
  padding: 8px;
}

.preview-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.preview-table th,
.preview-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid #334155;
}

.preview-table th {
  background: rgba(30, 41, 59, 0.8);
  color: #94a3b8;
  font-weight: 600;
  position: sticky;
  top: 0;
}

.preview-table td {
  color: #e2e8f0;
}

.preview-table tr:hover td {
  background: rgba(71, 85, 105, 0.2);
}

/* PDF Preview */
.preview-pdf {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pdf-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #64748b;
}

.view-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  color: #a78bfa;
  font-size: 13px;
  text-decoration: none;
  transition: all 0.2s;
}

.view-btn:hover {
  background: rgba(139, 92, 246, 0.25);
}

/* Fallback */
.preview-fallback {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

.preview-fallback pre {
  margin: 0;
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 12px;
  color: #94a3b8;
  white-space: pre-wrap;
}

/* Meta Info */
.preview-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 12px;
  background: rgba(30, 41, 59, 0.5);
  border-top: 1px solid #334155;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #64748b;
}

.meta-item.success {
  color: #34d399;
}
</style>

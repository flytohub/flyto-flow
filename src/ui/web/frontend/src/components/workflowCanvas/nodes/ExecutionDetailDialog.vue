<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="output-dialog-overlay" @click.self="$emit('close')">
        <div class="output-dialog">
          <div class="dialog-header">
            <span class="dialog-title">
              <Clock :size="16" />
              {{ label }} - {{ duration }}
            </span>
            <button class="close-btn" aria-label="Close" @click="$emit('close')">
              <X :size="18" />
            </button>
          </div>

          <div class="dialog-content">
            <!-- Error Display -->
            <div v-if="nodeError" class="error-section">
              <div class="section-label">Error</div>
              <div class="error-message">{{ typeof nodeError === 'string' ? nodeError : (nodeError.message || nodeError.error || 'Unknown error') }}</div>
              <pre v-if="nodeError.traceback || nodeError.stack" class="traceback">{{ nodeError.traceback || nodeError.stack }}</pre>
            </div>

            <!-- Display Outputs Gallery (priority: uses untruncated data) -->
            <div v-if="filteredDisplayOutputs.length > 0" class="gallery-section">
              <div class="section-label">Display Outputs</div>
              <div class="gallery-scroll">
                <div
                  v-for="(item, index) in filteredDisplayOutputs"
                  :key="index"
                  class="gallery-item"
                >
                  <!-- Item header -->
                  <div class="gallery-item-header">
                    <span class="type-badge" :class="item.type">{{ item.type }}</span>
                    <span class="item-title">{{ cleanTitle(item, index) }}</span>
                    <AlertTriangle
                      v-if="item.validation_warning"
                      :size="12"
                      class="warning-icon"
                      :title="item.validation_warning"
                    />
                    <!-- JSON toolbar -->
                    <template v-if="item.type === 'json'">
                      <button
                        class="json-toggle-btn"
                        @click="toggleJsonExpand(index)"
                        :title="jsonExpandedMap[index] ? 'Collapse' : 'Expand'"
                      >
                        {{ jsonExpandedMap[index] ? 'Collapse' : 'Expand' }}
                      </button>
                      <button class="json-copy-btn" :class="{ copied: copiedMap['gallery-json-' + index] }" @click="copyJson(item, 'gallery-json-' + index)" title="Copy JSON">
                        <Check v-if="copiedMap['gallery-json-' + index]" :size="12" />
                        <Copy v-else :size="12" />
                      </button>
                    </template>
                    <!-- Text copy button -->
                    <button
                      v-else-if="item.type === 'text' || item.type === 'auto' || (!item.type && item.content)"
                      class="json-copy-btn"
                      :class="{ copied: copiedMap['gallery-text-' + index] }"
                      @click="copyText(String(item.content || ''), 'gallery-text-' + index)"
                      title="Copy"
                    >
                      <Check v-if="copiedMap['gallery-text-' + index]" :size="12" />
                      <Copy v-else :size="12" />
                    </button>
                    <button
                      v-if="getDataUri(item)"
                      class="download-btn"
                      @click="handleDownload(item, index)"
                      title="Download"
                    >
                      <Download :size="14" />
                    </button>
                  </div>

                  <!-- Item content -->
                  <div class="gallery-item-content">
                    <!-- Image -->
                    <template v-if="item.type === 'image'">
                      <div v-if="getDataUri(item)" class="image-wrapper">
                        <img :src="getDataUri(item)" :alt="cleanTitle(item, index)" loading="lazy" />
                      </div>
                      <div v-else class="preview-fallback">Image data not available</div>
                    </template>

                    <!-- PDF -->
                    <div v-else-if="item.type === 'pdf'" class="preview-pdf">
                      <a :href="getDataUri(item)" :download="getFilename(item, index, 'pdf')" class="pdf-link">
                        Download PDF
                      </a>
                    </div>

                    <!-- HTML -->
                    <div v-else-if="item.type === 'html'" class="preview-html" v-html="sanitizeHtml(item.content)" />

                    <!-- JSON -->
                    <div v-else-if="item.type === 'json'" class="json-tree" :class="{ expanded: jsonExpandedMap[index] }">
                      <pre class="preview-text">{{ formatJsonContent(item.content) }}</pre>
                    </div>

                    <!-- Auto (smart detection) -->
                    <template v-else-if="item.type === 'auto'">
                      <div v-if="isDataUri(item.content)" class="image-wrapper">
                        <img :src="item.content" :alt="cleanTitle(item, index)" loading="lazy" />
                      </div>
                      <div v-else-if="isJsonLike(item.content)" class="json-tree" :class="{ expanded: jsonExpandedMap[index] }">
                        <pre class="preview-text">{{ formatJsonContent(item.content) }}</pre>
                      </div>
                      <pre v-else class="preview-text">{{ item.content || '(empty)' }}</pre>
                    </template>

                    <!-- Text / fallback -->
                    <pre v-else class="preview-text">{{ item.content || item.dataUri || item.data_uri || '(empty)' }}</pre>
                  </div>
                </div>
              </div>
            </div>

            <!-- Fallback: Inline image from nodeOutput (backward compat) -->
            <div v-else-if="outputImageUri" class="data-section">
              <div class="section-label">Output</div>
              <div class="image-wrapper">
                <img :src="outputImageUri" alt="Output image" />
              </div>
              <pre class="json-view">{{ formatJson(outputForDisplay) }}</pre>
            </div>

            <!-- Input Display -->
            <div v-if="nodeInput" class="data-section">
              <div class="section-label-row">
                <span class="section-label">Input</span>
                <button class="section-copy-btn" :class="{ copied: copiedMap['input'] }" @click="copyText(formatJson(nodeInput), 'input')" title="Copy">
                  <Check v-if="copiedMap['input']" :size="12" />
                  <Copy v-else :size="12" />
                </button>
              </div>
              <pre class="json-view">{{ formatJson(nodeInput) }}</pre>
            </div>

            <!-- Output Display (JSON) -->
            <div v-if="nodeOutput && !filteredDisplayOutputs.length" class="data-section">
              <div class="section-label-row">
                <span class="section-label">Output</span>
                <button class="section-copy-btn" :class="{ copied: copiedMap['output'] }" @click="copyText(formatJson(outputForDisplay), 'output')" title="Copy">
                  <Check v-if="copiedMap['output']" :size="12" />
                  <Copy v-else :size="12" />
                </button>
                <button
                  v-if="outputDownloadUrl"
                  class="section-copy-btn"
                  title="Download file"
                  @click="downloadWithAuth(outputDownloadUrl, outputDownloadFilename)"
                >
                  <Download :size="12" />
                </button>
              </div>
              <pre class="json-view">{{ formatJson(outputForDisplay) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { Clock, X, Download, Copy, Check, AlertTriangle } from 'lucide-vue-next'
import DOMPurify from 'dompurify'
import { authAPI } from '@/api/auth'

const props = defineProps({
  show: { type: Boolean, default: false },
  label: { type: String, default: '' },
  duration: { type: String, default: '' },
  nodeOutput: { type: [Object, Array, String, Number, Boolean], default: null },
  nodeInput: { type: [Object, Array, String, Number, Boolean], default: null },
  nodeError: { type: [Object, String], default: null },
  displayOutputs: { type: Array, default: () => [] }
})

defineEmits(['close'])

/** Filter out display outputs with unresolved variable titles (e.g. from loop body running before context is set) */
const filteredDisplayOutputs = computed(() =>
  (props.displayOutputs || []).filter(item => {
    const title = item.title || ''
    return !title.startsWith('${')
  })
)

/** Track expanded state per gallery item */
const jsonExpandedMap = reactive({})

/** Extract data_uri from output if present (for fallback image preview) */
const outputImageUri = computed(() => {
  const out = props.nodeOutput
  if (out && typeof out === 'object') {
    return out.dataUri || out.data_uri || null
  }
  return null
})

/** Output without base64/data_uri fields (too noisy for JSON view) */
const outputForDisplay = computed(() => {
  const out = props.nodeOutput
  if (out && typeof out === 'object' && (out.data_uri || out.dataUri)) {
    const { base64, data_uri, dataUri, ...rest } = out
    return rest
  }
  return out
})

/** Download URL from file_output post-processor (if step produced a file) */
const outputDownloadUrl = computed(() => {
  const out = props.nodeOutput
  if (out && typeof out === 'object') {
    return out.download_url || null
  }
  return null
})

const outputDownloadFilename = computed(() => {
  const out = props.nodeOutput
  return (out && out.download_filename) || 'download'
})

const _isDesktop = !!window.__TAURI_INTERNALS__

function _authHeaders() {
  // Goes through authAPI — returns null for expired / malformed tokens so we
  // don't leak stale Bearer headers into download requests.
  const token = authAPI.getAccessToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/** Download or open a file depending on Desktop/Cloud mode */
async function downloadWithAuth(url, filename) {
  try {
    if (_isDesktop) {
      // Desktop: open file directly with OS default app
      const filePath = new URL(url, window.location.origin).searchParams.get('path')
      if (filePath) {
        await fetch(`/api/files/open?path=${encodeURIComponent(filePath)}`, {
          method: 'POST', headers: _authHeaders(),
        })
        return
      }
    }

    // Cloud: fetch with auth → blob → download
    const resp = await fetch(url, { headers: _authHeaders() })
    if (!resp.ok) throw new Error(`Download failed: ${resp.status}`)
    const blob = await resp.blob()
    const blobUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(blobUrl)
  } catch (e) {
    console.error('Download failed:', e)
  }
}

function cleanTitle(item, index) {
  const title = item.title || ''
  if (!title || title.startsWith('${')) return `#${index + 1}`
  return title
}

function getDataUri(item) {
  // Server-side download URL (from file_output post-processor)
  if (item.download_url) return item.download_url

  const uri = item.dataUri || item.data_uri || ''
  const content = item.content || ''
  if (uri && uri.startsWith('data:')) return uri
  if (typeof content === 'string' && content.startsWith('data:')) return content
  // Raw base64 without prefix
  if (uri && uri.length > 100 && !uri.startsWith('$')) {
    return `data:image/png;base64,${uri}`
  }
  if (typeof content === 'string' && content.length > 100 && !content.startsWith('$') && item.type === 'image') {
    return `data:image/png;base64,${content}`
  }
  return null
}

function getFilename(item, index, ext) {
  const title = cleanTitle(item, index)
  const base = title.replace(/[^a-zA-Z0-9_-]/g, '_') || `output_${index + 1}`
  return `${base}.${ext}`
}

function handleDownload(item, index) {
  const uri = getDataUri(item)
  if (!uri) return

  // Server-side download URL — fetch with auth then trigger download
  if (item.download_url) {
    downloadWithAuth(item.download_url, item.download_filename || 'download')
    return
  }

  const ext = item.type === 'pdf' ? 'pdf' : 'png'
  const filename = item.download_filename || getFilename(item, index, ext)
  const link = document.createElement('a')
  link.href = uri
  link.download = filename
  link.click()
}

function formatJson(data) {
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

function formatJsonContent(content) {
  if (content && typeof content === 'object') {
    return JSON.stringify(content, null, 2)
  }
  if (typeof content === 'string') {
    try {
      return JSON.stringify(JSON.parse(content), null, 2)
    } catch {
      return content
    }
  }
  return String(content ?? '')
}

function isDataUri(content) {
  return typeof content === 'string' && content.startsWith('data:image/')
}

function isJsonLike(content) {
  if (content && typeof content === 'object') return true
  if (typeof content !== 'string') return false
  const trimmed = content.trim()
  return (trimmed.startsWith('{') && trimmed.endsWith('}')) ||
         (trimmed.startsWith('[') && trimmed.endsWith(']'))
}

function toggleJsonExpand(index) {
  jsonExpandedMap[index] = !jsonExpandedMap[index]
}

/** Track which button was just copied (key → true for 1.5s) */
const copiedMap = reactive({})

function setCopied(key) {
  copiedMap[key] = true
  setTimeout(() => { copiedMap[key] = false }, 1500)
}

function copyJson(item, key = 'json') {
  const text = formatJsonContent(item.content)
  navigator.clipboard.writeText(text).then(() => setCopied(key)).catch(() => {})
}

function copyText(text, key = 'text') {
  navigator.clipboard.writeText(text).then(() => setCopied(key)).catch(() => {})
}

function sanitizeHtml(html) {
  if (!html) return ''
  return DOMPurify.sanitize(html)
}
</script>

<style scoped>
.output-dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(2px);
}

.output-dialog {
  width: 90vw;
  max-width: 700px;
  max-height: 80vh;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  background: #0f172a;
  border-bottom: 1px solid #334155;
  flex-shrink: 0;
}

.dialog-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
}

.close-btn:hover {
  background: rgba(51, 65, 85, 0.5);
  color: #e2e8f0;
}

.dialog-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.section-label-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.section-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #64748b;
  margin-bottom: 6px;
}

.section-label-row .section-label {
  margin-bottom: 0;
}

.section-copy-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: 1px solid #475569;
  border-radius: 4px;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s ease;
}

.section-copy-btn:hover {
  background: rgba(59, 130, 246, 0.15);
  border-color: #3b82f6;
  color: #60a5fa;
}

.error-section {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  padding: 12px;
}

.error-message {
  color: #f87171;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.5;
  word-break: break-word;
}

.traceback {
  margin-top: 10px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #fca5a5;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow: auto;
}

/* ========== Gallery Section ========== */
.gallery-section {
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 12px;
}

.gallery-scroll {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.gallery-scroll::-webkit-scrollbar { width: 6px; }
.gallery-scroll::-webkit-scrollbar-track { background: transparent; }
.gallery-scroll::-webkit-scrollbar-thumb { background: #475569; border-radius: 3px; }
.gallery-scroll::-webkit-scrollbar-thumb:hover { background: #64748b; }

.gallery-item {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid #334155;
  border-radius: 8px;
  overflow: hidden;
}

.gallery-item:hover {
  border-color: #475569;
}

.gallery-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(51, 65, 85, 0.4);
}

.type-badge {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 2px 6px;
  border-radius: 4px;
  color: #ffffff;
  flex-shrink: 0;
}

.type-badge.image { background: #6366f1; }
.type-badge.pdf { background: #ef4444; }
.type-badge.text { background: #22c55e; }
.type-badge.html { background: #f59e0b; }
.type-badge.json { background: #3b82f6; }
.type-badge.auto { background: #8b5cf6; }
.type-badge.file { background: #64748b; }

.item-title {
  flex: 1;
  font-size: 12px;
  color: #cbd5e1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.warning-icon {
  color: #f59e0b;
  flex-shrink: 0;
}

.json-toggle-btn {
  font-size: 10px;
  padding: 2px 8px;
  border: 1px solid #475569;
  border-radius: 4px;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.json-toggle-btn:hover {
  background: rgba(59, 130, 246, 0.15);
  border-color: #3b82f6;
  color: #60a5fa;
}

.json-copy-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: 1px solid #475569;
  border-radius: 5px;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.json-copy-btn:hover {
  background: rgba(59, 130, 246, 0.15);
  border-color: #3b82f6;
  color: #60a5fa;
}

.json-copy-btn.copied,
.section-copy-btn.copied {
  border-color: #22c55e;
  color: #4ade80;
  background: rgba(34, 197, 94, 0.1);
}

.download-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: 1px solid #475569;
  border-radius: 5px;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.download-btn:hover {
  background: rgba(139, 92, 246, 0.15);
  border-color: #8b5cf6;
  color: #a78bfa;
}

.gallery-item-content {
  padding: 8px;
}

.image-wrapper {
  border-radius: 6px;
  background: #f8fafc;
}

.image-wrapper img {
  width: 100%;
  height: auto;
  display: block;
}

.preview-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  border-radius: 6px;
  background: rgba(51, 65, 85, 0.3);
  border: 1px dashed #475569;
  font-size: 12px;
  color: #64748b;
}

.preview-pdf {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.pdf-link {
  color: #60a5fa;
  font-size: 13px;
  text-decoration: none;
}

.pdf-link:hover { text-decoration: underline; }

.preview-html {
  color: #e2e8f0;
  font-size: 13px;
  line-height: 1.6;
  padding: 4px;
}

.preview-text {
  color: #e2e8f0;
  font-size: 12px;
  line-height: 1.5;
  font-family: 'JetBrains Mono', monospace;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
}

/* JSON tree with expand/collapse */
.json-tree {
  max-height: 200px;
  overflow: hidden;
  transition: max-height 0.2s ease;
}

.json-tree.expanded {
  max-height: none;
}

/* ========== Data Section (fallback / input / output) ========== */
.data-section {
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 12px;
}

.json-view {
  margin: 0;
  padding: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #94a3b8;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 250px;
  overflow: auto;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.fade-enter-active .output-dialog,
.fade-leave-active .output-dialog {
  transition: transform 0.15s ease;
}

.fade-enter-from .output-dialog,
.fade-leave-to .output-dialog {
  transform: scale(0.95);
}
</style>

<template>
  <div
    class="sticky-note"
    :class="{ selected, editing: isEditing }"
    :style="noteStyle"
  >
    <!-- Resize handle -->
    <div
      class="resize-handle"
      @mousedown.stop="startResize"
    />

    <!-- Delete button -->
    <button
      class="delete-btn"
      aria-label="Delete note"
      @click.stop="$emit('delete-node', { nodeId: id })"
    >
      <X :size="12" />
    </button>

    <!-- Color picker -->
    <div class="color-picker" v-if="showColorPicker">
      <button
        v-for="color in colors"
        :key="color.id"
        class="color-btn"
        :aria-label="color.id"
        :style="{ background: color.bg }"
        @click="changeColor(color.id)"
      />
    </div>
    <button
      class="color-toggle"
      aria-label="Change color"
      @click.stop="showColorPicker = !showColorPicker"
    >
      <Palette :size="12" />
    </button>

    <!-- Content (Markdown rendered) -->
    <div
      v-if="!isEditing"
      class="note-content"
      @dblclick="startEditing"
    >
      <h4 v-if="title" class="note-title">{{ title }}</h4>
      <div
        v-if="content"
        class="note-text markdown-body"
        v-html="renderedContent"
      />
      <p v-else class="note-text note-placeholder">
        {{ $t('node.sticky.placeholder', 'Double-click to edit...') }}
      </p>
    </div>

    <!-- Edit mode -->
    <div v-else class="note-editor">
      <input
        ref="titleInput"
        v-model="editTitle"
        class="title-input"
        :placeholder="$t('node.sticky.titlePlaceholder', 'Title (optional)')"
        @keydown.enter="$refs.contentInput.focus()"
      />
      <textarea
        ref="contentInput"
        v-model="editContent"
        class="content-input"
        :placeholder="$t('node.sticky.contentPlaceholder', 'Write your note here...')"
        @keydown.escape="cancelEditing"
        @blur="saveEditing"
      />
      <div class="editor-actions">
        <button class="save-btn" aria-label="Save" @click="saveEditing">
          <Check :size="14" />
        </button>
        <button class="cancel-btn" aria-label="Cancel" @click="cancelEditing">
          <X :size="14" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { X, Palette, Check } from 'lucide-vue-next'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

// Configure marked for sticky notes (simple, safe markdown)
marked.setOptions({
  breaks: true,
  gfm: true
})

const props = defineProps({
  id: String,
  data: Object,
  selected: Boolean
})

const emit = defineEmits(['delete-node', 'update-node'])

// Color options
const colors = [
  { id: 'yellow', bg: '#FEF3C7', text: '#92400E' },
  { id: 'green', bg: '#D1FAE5', text: '#065F46' },
  { id: 'blue', bg: '#DBEAFE', text: '#1E40AF' },
  { id: 'pink', bg: '#FCE7F3', text: '#9D174D' },
  { id: 'purple', bg: '#EDE9FE', text: '#5B21B6' },
  { id: 'gray', bg: '#F3F4F6', text: '#374151' }
]

// State
const isEditing = ref(false)
const showColorPicker = ref(false)
const editTitle = ref('')
const editContent = ref('')

const titleInput = ref(null)
const contentInput = ref(null)

// Get current color config
const currentColor = computed(() => {
  const colorId = props.data?.color || 'yellow'
  return colors.find(c => c.id === colorId) || colors[0]
})

// Style based on data
const noteStyle = computed(() => ({
  width: `${props.data?.width || 200}px`,
  height: `${props.data?.height || 150}px`,
  background: currentColor.value.bg,
  '--text-color': currentColor.value.text
}))

// Derived props
const title = computed(() => props.data?.title || '')
const content = computed(() => props.data?.content || '')

// Render markdown content with sanitization
const renderedContent = computed(() => {
  if (!content.value) return ''

  try {
    const rawHtml = marked.parse(content.value)
    // Sanitize HTML to prevent XSS
    return DOMPurify.sanitize(rawHtml, {
      ALLOWED_TAGS: ['p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'del', 'code', 'pre', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'hr'],
      ALLOWED_ATTR: ['href', 'target', 'rel']
    })
  } catch (e) {
    // Fallback to plain text if markdown parsing fails
    return content.value
  }
})

// Edit methods
function startEditing() {
  editTitle.value = title.value
  editContent.value = content.value
  isEditing.value = true
  nextTick(() => {
    contentInput.value?.focus()
  })
}

function saveEditing() {
  emit('update-node', {
    nodeId: props.id,
    updates: {
      title: editTitle.value,
      content: editContent.value
    }
  })
  isEditing.value = false
}

function cancelEditing() {
  isEditing.value = false
  editTitle.value = title.value
  editContent.value = content.value
}

function changeColor(colorId) {
  emit('update-node', {
    nodeId: props.id,
    updates: { color: colorId }
  })
  showColorPicker.value = false
}

// Resize handling
let resizeStart = null

function startResize(e) {
  resizeStart = {
    x: e.clientX,
    y: e.clientY,
    width: props.data?.width || 200,
    height: props.data?.height || 150
  }
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
}

function onResize(e) {
  if (!resizeStart) return
  const dx = e.clientX - resizeStart.x
  const dy = e.clientY - resizeStart.y
  const newWidth = Math.max(150, resizeStart.width + dx)
  const newHeight = Math.max(100, resizeStart.height + dy)

  emit('update-node', {
    nodeId: props.id,
    updates: {
      width: newWidth,
      height: newHeight
    }
  })
}

function stopResize() {
  resizeStart = null
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
}
</script>

<style scoped>
.sticky-note {
  position: relative;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 12px;
  cursor: move;
  transition: box-shadow 0.2s, transform 0.2s;
  color: var(--text-color);
  min-width: 150px;
  min-height: 100px;
}

.sticky-note:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.sticky-note.selected {
  box-shadow: 0 0 0 2px #8B5CF6, 0 4px 16px rgba(139, 92, 246, 0.3);
}

.sticky-note.editing {
  z-index: 100;
}

/* Resize handle */
.resize-handle {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 16px;
  height: 16px;
  cursor: se-resize;
  background: linear-gradient(135deg, transparent 50%, var(--text-color) 50%);
  opacity: 0.3;
  border-radius: 0 0 4px 0;
}

.sticky-note:hover .resize-handle {
  opacity: 0.6;
}

/* Delete button */
.delete-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #EF4444;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s;
  color: white;
  z-index: 10;
}

.sticky-note:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  transform: scale(1.1);
  background: #DC2626;
}

/* Color picker */
.color-toggle {
  position: absolute;
  top: -8px;
  left: -8px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #374151;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s;
  color: white;
  z-index: 10;
}

.sticky-note:hover .color-toggle {
  opacity: 1;
}

.color-picker {
  position: absolute;
  top: -8px;
  left: 16px;
  display: flex;
  gap: 4px;
  background: #1F2937;
  padding: 4px 8px;
  border-radius: 16px;
  z-index: 20;
}

.color-btn {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.color-btn:hover {
  transform: scale(1.2);
  border-color: white;
}

/* Content */
.note-content {
  height: 100%;
  overflow: hidden;
}

.note-title {
  margin: 0 0 8px 0;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.3;
}

.note-text {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  word-break: break-word;
}

.note-text.note-placeholder {
  opacity: 0.6;
  font-style: italic;
}

/* Markdown body styles */
.note-text.markdown-body {
  overflow: hidden;
}

.note-text.markdown-body :deep(p) {
  margin: 0 0 8px 0;
}

.note-text.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.note-text.markdown-body :deep(h1),
.note-text.markdown-body :deep(h2),
.note-text.markdown-body :deep(h3),
.note-text.markdown-body :deep(h4),
.note-text.markdown-body :deep(h5),
.note-text.markdown-body :deep(h6) {
  margin: 0 0 8px 0;
  font-weight: 600;
  line-height: 1.3;
}

.note-text.markdown-body :deep(h1) { font-size: 16px; }
.note-text.markdown-body :deep(h2) { font-size: 14px; }
.note-text.markdown-body :deep(h3) { font-size: 13px; }
.note-text.markdown-body :deep(h4),
.note-text.markdown-body :deep(h5),
.note-text.markdown-body :deep(h6) { font-size: 12px; }

.note-text.markdown-body :deep(ul),
.note-text.markdown-body :deep(ol) {
  margin: 0 0 8px 0;
  padding-left: 20px;
}

.note-text.markdown-body :deep(li) {
  margin: 2px 0;
}

.note-text.markdown-body :deep(code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 1px 4px;
  border-radius: 3px;
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 11px;
}

.note-text.markdown-body :deep(pre) {
  background: rgba(0, 0, 0, 0.1);
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 0 0 8px 0;
}

.note-text.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
}

.note-text.markdown-body :deep(blockquote) {
  margin: 0 0 8px 0;
  padding-left: 12px;
  border-left: 3px solid currentColor;
  opacity: 0.8;
}

.note-text.markdown-body :deep(a) {
  color: inherit;
  text-decoration: underline;
}

.note-text.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid currentColor;
  opacity: 0.3;
  margin: 8px 0;
}

.note-text.markdown-body :deep(strong),
.note-text.markdown-body :deep(b) {
  font-weight: 600;
}

.note-text.markdown-body :deep(em),
.note-text.markdown-body :deep(i) {
  font-style: italic;
}

.note-text.markdown-body :deep(s),
.note-text.markdown-body :deep(del) {
  text-decoration: line-through;
}

/* Editor */
.note-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 8px;
}

.title-input {
  width: 100%;
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.1);
  font-size: 13px;
  font-weight: 600;
  color: inherit;
}

.content-input {
  flex: 1;
  width: 100%;
  padding: 8px;
  border: none;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.1);
  font-size: 12px;
  line-height: 1.5;
  color: inherit;
  resize: none;
}

.title-input:focus,
.content-input:focus {
  outline: none;
  background: rgba(0, 0, 0, 0.15);
}

.editor-actions {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
}

.save-btn,
.cancel-btn {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.save-btn {
  background: #10B981;
  color: white;
}

.save-btn:hover {
  background: #059669;
}

.cancel-btn {
  background: #64748B;
  color: white;
}

.cancel-btn:hover {
  background: #475569;
}
</style>

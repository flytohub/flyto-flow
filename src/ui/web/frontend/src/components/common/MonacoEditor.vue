<template>
  <div ref="editorContainer" class="monaco-editor-wrapper">
    <div v-if="loading" class="monaco-loading-placeholder">
      <span class="monaco-loading-text">{{ t('common.loading') }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'

let monaco = null

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  language: {
    type: String,
    default: 'javascript'
  },
  theme: {
    type: String,
    default: 'vs-dark'
  },
  options: {
    type: Object,
    default: () => ({})
  },
  readOnly: {
    type: Boolean,
    default: false
  },
  height: {
    type: String,
    default: '300px'
  }
})

const emit = defineEmits(['update:modelValue', 'change', 'editor-mounted'])

const editorContainer = ref(null)
const loading = ref(true)
const { t } = useI18n()
let editor = null
let isUpdating = false

async function loadMonaco() {
  if (monaco) return monaco

  const [editorApi] = await Promise.all([
    import('monaco-editor/esm/vs/editor/editor.api'),
    import('monaco-editor/esm/vs/basic-languages/javascript/javascript.contribution'),
    import('monaco-editor/esm/vs/basic-languages/python/python.contribution')
  ])
  monaco = editorApi
  return monaco
}

// Default editor options optimized for workflow code editing
const defaultOptions = {
  minimap: { enabled: false },
  fontSize: 13,
  fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
  lineNumbers: 'on',
  scrollBeyondLastLine: false,
  automaticLayout: true,
  tabSize: 2,
  wordWrap: 'on',
  renderWhitespace: 'selection',
  bracketPairColorization: { enabled: true },
  scrollbar: {
    vertical: 'auto',
    horizontal: 'auto',
    verticalScrollbarSize: 8,
    horizontalScrollbarSize: 8
  },
  padding: { top: 8, bottom: 8 },
  lineDecorationsWidth: 0,
  lineNumbersMinChars: 3,
  glyphMargin: false,
  folding: true,
  contextmenu: true,
  quickSuggestions: true,
  suggestOnTriggerCharacters: true
}

onMounted(async () => {
  await nextTick()

  if (!editorContainer.value) return

  // Set custom CSS variable for height
  editorContainer.value.style.height = props.height

  // Lazy-load the editor only when the component actually mounts. Import the
  // editor API plus the two languages exposed by CodeNodeParams instead of the
  // all-language Monaco package.
  monaco = await loadMonaco()
  loading.value = false

  // Merge options
  const mergedOptions = {
    ...defaultOptions,
    ...props.options,
    value: props.modelValue,
    language: props.language,
    theme: props.theme,
    readOnly: props.readOnly
  }

  // Create editor instance
  editor = monaco.editor.create(editorContainer.value, mergedOptions)

  // Listen for content changes
  editor.onDidChangeModelContent(() => {
    if (isUpdating) return

    const value = editor.getValue()
    emit('update:modelValue', value)
    emit('change', value)
  })

  // Emit mounted event with editor instance for advanced usage
  emit('editor-mounted', editor)
})

// Watch for external value changes
watch(() => props.modelValue, (newValue) => {
  if (!editor) return

  const currentValue = editor.getValue()
  if (newValue !== currentValue) {
    isUpdating = true
    editor.setValue(newValue || '')
    isUpdating = false
  }
})

// Watch for language changes
watch(() => props.language, (newLang) => {
  if (!editor) return

  const model = editor.getModel()
  if (model) {
    monaco.editor.setModelLanguage(model, newLang)
  }
})

// Watch for theme changes
watch(() => props.theme, (newTheme) => {
  if (!editor) return
  monaco.editor.setTheme(newTheme)
})

// Watch for readOnly changes
watch(() => props.readOnly, (newReadOnly) => {
  if (!editor) return
  editor.updateOptions({ readOnly: newReadOnly })
})

// Watch for height changes
watch(() => props.height, (newHeight) => {
  if (editorContainer.value) {
    editorContainer.value.style.height = newHeight
    editor?.layout()
  }
})

// Expose methods for parent component access
const focus = () => editor?.focus()
const getValue = () => editor?.getValue() || ''
const setValue = (value) => {
  if (editor) {
    isUpdating = true
    editor.setValue(value)
    isUpdating = false
  }
}
const getEditor = () => editor
const layout = () => editor?.layout()

defineExpose({
  focus,
  getValue,
  setValue,
  getEditor,
  layout
})

onUnmounted(() => {
  editor?.dispose()
  editor = null
})
</script>

<style scoped>
.monaco-editor-wrapper {
  width: 100%;
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 8px;
  overflow: hidden;
  background: #1e1e1e;
}

/* Override Monaco's default styles for better integration */
.monaco-editor-wrapper :deep(.monaco-editor) {
  border-radius: 8px;
}

.monaco-editor-wrapper :deep(.monaco-editor .margin) {
  background: #1e1e1e;
}

.monaco-editor-wrapper :deep(.monaco-editor .monaco-editor-background) {
  background: #1e1e1e;
}

.monaco-loading-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 120px;
  background: #1e1e1e;
  color: #888;
  font-size: 13px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
}
</style>

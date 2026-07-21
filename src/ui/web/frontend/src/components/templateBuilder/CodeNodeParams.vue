<template>
  <div class="code-node-params">
    <!-- Language Selector -->
    <div class="param-field">
      <label class="param-label">
        <Code2 :size="14" />
        {{ $t('code.language') }}
      </label>
      <div class="language-tabs">
        <button
          v-for="lang in languages"
          :key="lang.value"
          class="language-tab"
          :class="{ active: localParams.language === lang.value }"
          :disabled="readOnly"
          @click="setLanguage(lang.value)"
        >
          <component :is="lang.icon" :size="14" />
          {{ lang.label }}
        </button>
      </div>
    </div>

    <!-- Monaco Editor -->
    <div class="param-field editor-field">
      <label class="param-label">
        <FileCode :size="14" />
        {{ $t('code.sourceCode') }}
      </label>
      <div class="editor-container">
        <MonacoEditor
          v-model="localParams.code"
          :language="monacoLanguage"
          :read-only="readOnly"
          :height="editorHeight"
          @change="emitUpdate"
        />
      </div>
    </div>

    <!-- Available Variables Reference -->
    <div class="variables-reference">
      <div class="reference-header">
        <Variable :size="14" />
        <span>{{ $t('code.availableVariables') }}</span>
      </div>
      <div class="variable-list">
        <div class="variable-item" @click="insertVariable('$input.all()')">
          <code>$input.all()</code>
          <span class="variable-desc">{{ $t('code.inputAllDesc') }}</span>
        </div>
        <div class="variable-item" @click="insertVariable('$input.first()')">
          <code>$input.first()</code>
          <span class="variable-desc">{{ $t('code.inputFirstDesc') }}</span>
        </div>
        <div class="variable-item" @click="insertVariable('$json')">
          <code>$json</code>
          <span class="variable-desc">{{ $t('code.jsonDesc') }}</span>
        </div>
      </div>
    </div>

    <!-- Execution Notice -->
    <div class="execution-notice">
      <AlertCircle :size="14" />
      <span>{{ $t('code.localExecutionNotice') }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, markRaw } from 'vue'
import { useI18n } from 'vue-i18n'
import { Code2, FileCode, Variable, AlertCircle } from 'lucide-vue-next'
import MonacoEditor from '@/components/common/MonacoEditor.vue'

// Language icons - using simple text-based for now
const JsIcon = markRaw({
  template: '<span class="lang-icon js">JS</span>'
})
const PyIcon = markRaw({
  template: '<span class="lang-icon py">PY</span>'
})

const { t } = useI18n()

const props = defineProps({
  params: {
    type: Object,
    default: () => ({})
  },
  readOnly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:params'])

const localParams = ref({
  language: 'javascript',
  code: ''
})

const editorHeight = '280px'

// Language options
const languages = [
  {
    value: 'javascript',
    label: 'JavaScript',
    icon: JsIcon
  },
  {
    value: 'python',
    label: 'Python',
    icon: PyIcon
  }
]

// Map internal language to Monaco language ID
const monacoLanguage = computed(() => {
  return localParams.value.language === 'python' ? 'python' : 'javascript'
})

// Default code templates
const codeTemplates = {
  javascript: `// Access input from previous step
const items = $input.all();

// Process each item
for (const item of items) {
  item.processed = true;
}

// Return the result
return items;`,
  python: `# Access input from previous step
items = $input.all()

# Process each item
for item in items:
    item['processed'] = True

# Return the result
result = items`
}

function initParams() {
  localParams.value = {
    language: props.params?.language || 'javascript',
    code: props.params?.code || codeTemplates[props.params?.language || 'javascript']
  }
}

function setLanguage(lang) {
  if (props.readOnly) return

  const oldLang = localParams.value.language
  localParams.value.language = lang

  // If code is empty or is the default template, switch to new language template
  const oldTemplate = codeTemplates[oldLang]
  if (!localParams.value.code || localParams.value.code.trim() === oldTemplate.trim()) {
    localParams.value.code = codeTemplates[lang]
  }

  emitUpdate()
}

function insertVariable(variable) {
  // For now, just copy to clipboard or show a toast
  // In future, we can integrate with Monaco editor to insert at cursor
  navigator.clipboard?.writeText(variable)
}

function emitUpdate() {
  emit('update:params', { ...localParams.value })
}

watch(() => props.params, () => {
  initParams()
}, { deep: true })

onMounted(() => {
  initParams()
})
</script>

<style scoped>
.code-node-params {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 14px;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid #334155;
  border-radius: 8px;
}

.param-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
}

/* Language Tabs */
.language-tabs {
  display: flex;
  gap: 8px;
}

.language-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid #475569;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.6);
  color: #94a3b8;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.language-tab:hover:not(:disabled) {
  border-color: #8B5CF6;
  color: #e2e8f0;
}

.language-tab.active {
  border-color: #8B5CF6;
  background: rgba(139, 92, 246, 0.15);
  color: #c4b5fd;
}

.language-tab:disabled {
  opacity: 0.6;
  cursor: default;
}

/* Language Icons */
:deep(.lang-icon) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  font-size: 10px;
  font-weight: 700;
  border-radius: 4px;
}

:deep(.lang-icon.js) {
  background: #f7df1e;
  color: #323330;
}

:deep(.lang-icon.py) {
  background: linear-gradient(135deg, #3776ab 50%, #ffd43b 50%);
  color: white;
}

/* Editor Container */
.editor-field {
  flex: 1;
}

.editor-container {
  border-radius: 8px;
  overflow: hidden;
}

/* Variables Reference */
.variables-reference {
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid #334155;
  border-radius: 8px;
  overflow: hidden;
}

.reference-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  background: rgba(15, 23, 42, 0.6);
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.variable-list {
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.variable-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}

.variable-item:hover {
  background: rgba(139, 92, 246, 0.1);
}

.variable-item code {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 12px;
  padding: 2px 8px;
  background: rgba(139, 92, 246, 0.2);
  border-radius: 4px;
  color: #c4b5fd;
  white-space: nowrap;
}

.variable-desc {
  font-size: 11px;
  color: #64748b;
}

/* Execution Notice */
.execution-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 8px;
  font-size: 11px;
  color: #fbbf24;
}
</style>

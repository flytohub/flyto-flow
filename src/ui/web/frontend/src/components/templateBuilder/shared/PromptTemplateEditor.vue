/**
 * Prompt Template Editor
 *
 * Textarea with syntax highlighting for {{variable}} placeholders.
 * Shows detected variables and supports variable insertion.
 */
<template>
  <div class="prompt-template-editor">
    <!-- Label -->
    <label v-if="label" class="prompt-label">
      {{ label }}
      <span v-if="required" class="required-mark">*</span>
    </label>

    <!-- Editor container -->
    <div class="editor-container">
      <!-- Highlighted overlay (renders behind textarea) -->
      <div
        ref="overlayRef"
        class="highlight-overlay"
        aria-hidden="true"
      >
        <span
          v-for="(segment, i) in segments"
          :key="i"
          :class="segment.type"
        >{{ segment.text }}</span>
      </div>

      <!-- Actual textarea -->
      <textarea
        ref="textareaRef"
        v-model="localValue"
        @input="onInput"
        @scroll="syncScroll"
        @keydown="onKeydown"
        class="prompt-textarea"
        :placeholder="placeholder"
        :rows="rows"
        spellcheck="false"
      ></textarea>

      <!-- Variable insert button -->
      <button
        v-if="showVariableButton"
        type="button"
        class="variable-btn"
        :title="$t('llmChain.insertVariable')"
        @click="$emit('insert-variable')"
      >
        <Braces :size="14" />
      </button>
    </div>

    <!-- Detected variables display -->
    <div v-if="showDetectedVariables && detectedVariables.length > 0" class="detected-variables">
      <span class="detected-label">{{ $t('llmChain.detectedVariables') }}:</span>
      <span
        v-for="varName in detectedVariables"
        :key="varName"
        class="variable-tag"
      >
        {{ varName }}
      </span>
    </div>

    <!-- Hint text -->
    <p v-if="hint" class="hint-text">{{ hint }}</p>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { Braces } from 'lucide-vue-next'
import { extractVariables } from '@/utils/promptTemplate'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  label: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: ''
  },
  hint: {
    type: String,
    default: ''
  },
  rows: {
    type: Number,
    default: 4
  },
  required: {
    type: Boolean,
    default: false
  },
  showVariableButton: {
    type: Boolean,
    default: true
  },
  showDetectedVariables: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'insert-variable', 'cursor-change'])

const textareaRef = ref(null)
const overlayRef = ref(null)
const localValue = ref(props.modelValue)

// Variable pattern for {{variable}} syntax
const VARIABLE_PATTERN = /(\{\{[^}]+\}\})/g

// Extract detected variables
const detectedVariables = computed(() => {
  return extractVariables(localValue.value)
})

// Parse text into segments for highlighting
const segments = computed(() => {
  const text = localValue.value || ''
  if (!text) return [{ type: 'normal', text: '' }]

  const result = []
  let lastIndex = 0

  const matches = [...text.matchAll(VARIABLE_PATTERN)]

  for (const match of matches) {
    // Add normal text before the match
    if (match.index > lastIndex) {
      result.push({
        type: 'normal',
        text: text.slice(lastIndex, match.index)
      })
    }
    // Add the variable
    result.push({
      type: 'variable',
      text: match[0]
    })
    lastIndex = match.index + match[0].length
  }

  // Add remaining text
  if (lastIndex < text.length) {
    result.push({
      type: 'normal',
      text: text.slice(lastIndex)
    })
  }

  if (result.length === 0) {
    result.push({ type: 'normal', text: '' })
  }

  return result
})

// Sync with parent value
watch(() => props.modelValue, (newVal) => {
  if (newVal !== localValue.value) {
    localValue.value = newVal
  }
})

function onInput() {
  emit('update:modelValue', localValue.value)
}

function syncScroll() {
  if (overlayRef.value && textareaRef.value) {
    overlayRef.value.scrollTop = textareaRef.value.scrollTop
    overlayRef.value.scrollLeft = textareaRef.value.scrollLeft
  }
}

function onKeydown(e) {
  if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(e.key)) {
    nextTick(() => {
      if (textareaRef.value) {
        emit('cursor-change', {
          start: textareaRef.value.selectionStart,
          end: textareaRef.value.selectionEnd
        })
      }
    })
  }
}

/**
 * Insert text at current cursor position
 */
function insertAtCursor(text) {
  if (!textareaRef.value) return

  const textarea = textareaRef.value
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const before = localValue.value.slice(0, start)
  const after = localValue.value.slice(end)

  localValue.value = before + text + after
  emit('update:modelValue', localValue.value)

  nextTick(() => {
    const newPos = start + text.length
    textarea.setSelectionRange(newPos, newPos)
    textarea.focus()
  })
}

/**
 * Insert a variable placeholder
 */
function insertVariable(varName) {
  insertAtCursor(`{{${varName}}}`)
}

/**
 * Focus the textarea
 */
function focus() {
  textareaRef.value?.focus()
}

defineExpose({
  insertAtCursor,
  insertVariable,
  focus
})
</script>

<style scoped>
.prompt-template-editor {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.prompt-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  color: #94a3b8;
}

.required-mark {
  color: #f87171;
}

.editor-container {
  position: relative;
  font-family: 'SF Mono', Monaco, 'Fira Code', monospace;
  font-size: 13px;
  line-height: 1.6;
}

/* Overlay for syntax highlighting */
.highlight-overlay {
  position: absolute;
  inset: 0;
  padding: 10px 12px;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow: hidden;
  pointer-events: none;
  color: #e2e8f0;
  background: transparent;
  border-radius: 8px;
}

.highlight-overlay .variable {
  color: #a78bfa;
  background: rgba(139, 92, 246, 0.15);
  border-radius: 3px;
  padding: 0 2px;
  margin: 0 -2px;
}

.highlight-overlay .normal {
  color: #e2e8f0;
}

/* Actual textarea */
.prompt-textarea {
  position: relative;
  width: 100%;
  padding: 10px 12px;
  padding-right: 40px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 8px;
  color: transparent;
  caret-color: #8B5CF6;
  font-family: inherit;
  font-size: inherit;
  line-height: inherit;
  resize: vertical;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.prompt-textarea:focus {
  outline: none;
  border-color: rgba(139, 92, 246, 0.5);
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.1);
}

.prompt-textarea::placeholder {
  color: #475569;
}

.prompt-textarea::selection {
  background: rgba(139, 92, 246, 0.4);
  color: #e2e8f0;
}

/* Variable insert button */
.variable-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.variable-btn:hover {
  background: rgba(139, 92, 246, 0.2);
  border-color: rgba(139, 92, 246, 0.4);
  color: #a78bfa;
}

/* Detected variables */
.detected-variables {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  background: rgba(15, 23, 42, 0.4);
  border-radius: 6px;
  font-size: 11px;
}

.detected-label {
  color: #64748b;
}

.variable-tag {
  padding: 2px 8px;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 4px;
  color: #a78bfa;
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 11px;
}

/* Hint text */
.hint-text {
  margin: 0;
  font-size: 11px;
  color: #64748b;
}
</style>

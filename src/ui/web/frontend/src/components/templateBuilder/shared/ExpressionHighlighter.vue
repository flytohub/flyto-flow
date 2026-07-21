<template>
  <div
    class="expression-highlighter"
    :class="{ 'drag-over': isDragOver }"
    @dragenter.prevent="onDragEnter"
    @dragover.prevent="onDragOver"
    @dragleave="onDragLeave"
    @drop.prevent="onDrop"
  >
    <!-- Highlighted overlay (renders behind textarea for syntax coloring) -->
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

    <!-- Actual textarea for editing -->
    <textarea
      ref="textareaRef"
      v-model="localValue"
      @input="onInput"
      @scroll="syncScroll"
      @keydown="onKeydown"
      @select="onSelectionChange"
      @click="onSelectionChange"
      class="expression-textarea"
      :placeholder="placeholder"
      spellcheck="false"
    ></textarea>

    <!-- Autocomplete dropdown -->
    <Transition name="dropdown">
      <div
        v-if="showAutocomplete && filteredSuggestions.length > 0"
        ref="autocompleteRef"
        class="autocomplete-dropdown"
        :style="autocompletePosition"
      >
        <button
          v-for="(suggestion, i) in filteredSuggestions"
          :key="suggestion.expression"
          class="autocomplete-item"
          :class="{ 'selected': i === selectedIndex }"
          @click="insertSuggestion(suggestion)"
          @mouseenter="selectedIndex = i"
        >
          <span class="suggestion-icon" :style="{ color: suggestion.color }">
            <component :is="getSuggestionIcon(suggestion.category)" :size="14" />
          </span>
          <span class="suggestion-text">
            <span class="suggestion-name">{{ suggestion.name }}</span>
            <span class="suggestion-path">{{ suggestion.expression }}</span>
          </span>
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { FormInput, Layers, Settings, Hash } from 'lucide-vue-next'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '${ui.inputs.name}'
  },
  // Available variables for autocomplete
  suggestions: {
    type: Array,
    default: () => []
    // Expected format: [{ name: 'fieldName', expression: '${ui.inputs.fieldName}', category: 'inputs', color: '#...' }]
  }
})

const emit = defineEmits(['update:modelValue', 'cursor-change'])

const textareaRef = ref(null)
const overlayRef = ref(null)
const autocompleteRef = ref(null)
const localValue = ref(props.modelValue)

// Autocomplete state
const showAutocomplete = ref(false)

// Drag-drop state
const isDragOver = ref(false)
const dragEnterCount = ref(0)
const selectedIndex = ref(0)
const autocompletePosition = ref({ top: '0px', left: '0px' })
const currentPrefix = ref('')

// Variable pattern for syntax highlighting
const VARIABLE_PATTERN = /(\$\{[^}]*\})/g

// Parse text into segments for highlighting
const segments = computed(() => {
  const text = localValue.value || ''
  if (!text) return [{ type: 'normal', text: '' }]

  const result = []
  let lastIndex = 0

  // Split by variable pattern
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

  // Ensure we have at least one segment
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

// Filter suggestions based on current input
const filteredSuggestions = computed(() => {
  if (!showAutocomplete.value || !currentPrefix.value) {
    return props.suggestions.slice(0, 10)
  }

  const prefix = currentPrefix.value.toLowerCase()
  return props.suggestions
    .filter(s => {
      const name = (s.name || '').toLowerCase()
      const expr = (s.expression || '').toLowerCase()
      return name.includes(prefix) || expr.includes(prefix)
    })
    .slice(0, 10)
})

// Get icon for suggestion category
function getSuggestionIcon(category) {
  switch (category) {
    case 'inputs':
      return FormInput
    case 'steps':
      return Layers
    case 'env':
      return Settings
    default:
      return Hash
  }
}

// Check if cursor is inside an incomplete variable expression
function checkForAutocomplete() {
  if (!textareaRef.value) return

  const textarea = textareaRef.value
  const cursorPos = textarea.selectionStart
  const textBeforeCursor = localValue.value.slice(0, cursorPos)

  // Find the last ${ before cursor
  const lastOpen = textBeforeCursor.lastIndexOf('${')
  if (lastOpen === -1) {
    showAutocomplete.value = false
    return
  }

  // Check if there's a closing } after the ${
  const textAfterOpen = textBeforeCursor.slice(lastOpen)
  if (textAfterOpen.includes('}')) {
    showAutocomplete.value = false
    return
  }

  // Extract the partial variable name (after ${)
  currentPrefix.value = textAfterOpen.slice(2)
  selectedIndex.value = 0
  showAutocomplete.value = true

  // Position the dropdown
  updateAutocompletePosition(cursorPos)
}

// Update dropdown position based on cursor
function updateAutocompletePosition(cursorPos) {
  if (!textareaRef.value) return

  const textarea = textareaRef.value
  const textBeforeCursor = localValue.value.slice(0, cursorPos)
  const lines = textBeforeCursor.split('\n')
  const currentLine = lines.length - 1
  const currentCol = lines[lines.length - 1].length

  // Approximate character dimensions
  const charWidth = 8.4  // monospace font
  const lineHeight = 22.4  // 14px * 1.6

  autocompletePosition.value = {
    top: `${(currentLine + 1) * lineHeight + 12 + 4}px`,
    left: `${currentCol * charWidth + 12}px`
  }
}

// Insert selected suggestion
function insertSuggestion(suggestion) {
  if (!textareaRef.value || !suggestion) return

  const textarea = textareaRef.value
  const cursorPos = textarea.selectionStart
  const textBeforeCursor = localValue.value.slice(0, cursorPos)

  // Find where the ${ starts
  const lastOpen = textBeforeCursor.lastIndexOf('${')
  if (lastOpen === -1) return

  // Replace from ${ to cursor with the full expression
  const before = localValue.value.slice(0, lastOpen)
  const after = localValue.value.slice(cursorPos)

  localValue.value = before + suggestion.expression + after
  emit('update:modelValue', localValue.value)

  showAutocomplete.value = false

  // Set cursor after the inserted expression
  nextTick(() => {
    const newPos = lastOpen + suggestion.expression.length
    textarea.setSelectionRange(newPos, newPos)
    textarea.focus()
  })
}

// Close autocomplete on outside click
function handleClickOutside(e) {
  if (autocompleteRef.value && !autocompleteRef.value.contains(e.target)) {
    showAutocomplete.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

function onInput() {
  emit('update:modelValue', localValue.value)
  // Check for autocomplete trigger
  nextTick(checkForAutocomplete)
}

function syncScroll() {
  if (overlayRef.value && textareaRef.value) {
    overlayRef.value.scrollTop = textareaRef.value.scrollTop
    overlayRef.value.scrollLeft = textareaRef.value.scrollLeft
  }
}

function onSelectionChange() {
  if (textareaRef.value) {
    emit('cursor-change', {
      start: textareaRef.value.selectionStart,
      end: textareaRef.value.selectionEnd
    })
  }
}

function onKeydown(e) {
  // Handle autocomplete navigation
  if (showAutocomplete.value && filteredSuggestions.value.length > 0) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      selectedIndex.value = (selectedIndex.value + 1) % filteredSuggestions.value.length
      return
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      selectedIndex.value = selectedIndex.value > 0
        ? selectedIndex.value - 1
        : filteredSuggestions.value.length - 1
      return
    }
    if (e.key === 'Enter' || e.key === 'Tab') {
      e.preventDefault()
      insertSuggestion(filteredSuggestions.value[selectedIndex.value])
      return
    }
    if (e.key === 'Escape') {
      e.preventDefault()
      showAutocomplete.value = false
      return
    }
  }

  // Emit cursor change on arrow keys
  if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(e.key)) {
    nextTick(onSelectionChange)
  }
}

/**
 * Insert text at current cursor position
 * Called externally via ref
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

  // Set cursor after inserted text
  nextTick(() => {
    const newPos = start + text.length
    textarea.setSelectionRange(newPos, newPos)
    textarea.focus()
    onSelectionChange()
  })
}

/**
 * Focus the textarea
 */
function focus() {
  textareaRef.value?.focus()
}

/**
 * Drag-drop handlers for variable insertion
 */
function onDragEnter(e) {
  // Only accept flyto variable drag data
  if (e.dataTransfer.types.includes('application/x-flyto-variable') ||
      e.dataTransfer.types.includes('text/plain')) {
    dragEnterCount.value++
    isDragOver.value = true
  }
}

function onDragOver(e) {
  // Required to allow drop
  if (e.dataTransfer.types.includes('application/x-flyto-variable') ||
      e.dataTransfer.types.includes('text/plain')) {
    e.dataTransfer.dropEffect = 'copy'
  }
}

function onDragLeave(e) {
  dragEnterCount.value--
  if (dragEnterCount.value <= 0) {
    isDragOver.value = false
    dragEnterCount.value = 0
  }
}

function onDrop(e) {
  isDragOver.value = false
  dragEnterCount.value = 0

  // Try to get structured variable data first
  const variableJson = e.dataTransfer.getData('application/x-flyto-variable')
  if (variableJson) {
    try {
      const variable = JSON.parse(variableJson)
      if (variable.expression) {
        insertAtCursor(variable.expression)
        return
      }
    } catch (err) {
    }
  }

  // Fallback to plain text
  const plainText = e.dataTransfer.getData('text/plain')
  if (plainText) {
    insertAtCursor(plainText)
  }
}

// Expose methods for parent component
defineExpose({
  insertAtCursor,
  focus
})
</script>

<style scoped>
.expression-highlighter {
  position: relative;
  font-family: 'SF Mono', Monaco, 'Fira Code', monospace;
  font-size: 14px;
  line-height: 1.6;
}

/* Overlay for syntax highlighting */
.highlight-overlay {
  position: absolute;
  inset: 0;
  padding: 12px;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow: hidden;
  pointer-events: none;
  color: #e2e8f0;
  background: transparent;
}

/* Variable highlighting */
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

/* Actual textarea - transparent to show overlay */
.expression-textarea {
  position: relative;
  width: 100%;
  min-height: 120px;
  padding: 12px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 8px;
  color: transparent;
  caret-color: #8B5CF6;
  font-family: inherit;
  font-size: inherit;
  line-height: inherit;
  resize: vertical;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.expression-textarea:focus {
  outline: none;
  border-color: #8B5CF6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.expression-textarea::placeholder {
  color: #475569;
}

/* Selection styling - needs to be visible */
.expression-textarea::selection {
  background: rgba(139, 92, 246, 0.4);
  color: #e2e8f0;
}

/* Autocomplete dropdown */
.autocomplete-dropdown {
  position: absolute;
  min-width: 280px;
  max-width: 400px;
  max-height: 240px;
  overflow-y: auto;
  background: #1e293b;
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), 0 0 16px rgba(139, 92, 246, 0.15);
  z-index: 100;
}

.autocomplete-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 12px;
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
}

.autocomplete-item:hover,
.autocomplete-item.selected {
  background: rgba(139, 92, 246, 0.2);
}

.autocomplete-item:first-child {
  border-radius: 7px 7px 0 0;
}

.autocomplete-item:last-child {
  border-radius: 0 0 7px 7px;
}

.autocomplete-item:only-child {
  border-radius: 7px;
}

.suggestion-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: rgba(139, 92, 246, 0.15);
  border-radius: 6px;
  flex-shrink: 0;
}

.suggestion-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.suggestion-name {
  font-size: 13px;
  font-weight: 500;
  color: #f1f5f9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.suggestion-path {
  font-size: 11px;
  font-family: 'SF Mono', Monaco, 'Fira Code', monospace;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Dropdown animation */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Scrollbar for autocomplete */
.autocomplete-dropdown::-webkit-scrollbar {
  width: 4px;
}

.autocomplete-dropdown::-webkit-scrollbar-track {
  background: transparent;
}

.autocomplete-dropdown::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.4);
  border-radius: 2px;
}

/* Drag-over state */
.expression-highlighter.drag-over .expression-textarea {
  border-color: #8B5CF6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.25), inset 0 0 20px rgba(139, 92, 246, 0.1);
}

.expression-highlighter.drag-over::before {
  content: '';
  position: absolute;
  inset: 0;
  border: 2px dashed #8B5CF6;
  border-radius: 8px;
  pointer-events: none;
  z-index: 10;
  animation: drag-pulse 1s ease-in-out infinite;
}

@keyframes drag-pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}
</style>

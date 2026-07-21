<template>
  <div class="simple-tool-view">
    <!-- Tool Header -->
    <ToolHeader
      :tool="tool"
      :show-advanced-toggle="showAdvancedToggle"
      @toggle-advanced="$emit('toggle-advanced')"
    />

    <!-- Main Content: Input -> Process -> Output -->
    <div class="tool-flow">
      <!-- INPUT SECTION -->
      <div class="flow-section input-section">
        <div class="section-label">
          <Upload :size="18" />
          <span>{{ $t('simpleToolView.input') }}</span>
        </div>

        <!-- Schema-driven input form -->
        <div v-if="useAutoForm && Object.keys(paramsSchema).length > 0" class="auto-form-wrapper">
          <SchemaParamsRenderer
            :schema="paramsSchema"
            v-model="inputValues"
            visibility-mode="simple"
            compact
          />
        </div>

        <!-- Fallback: Manual input cards -->
        <div v-else class="input-cards">
          <div
            v-for="field in inputFields"
            :key="field.key"
            class="input-card"
            :class="{ 'has-value': hasValue(field.key), 'is-file': isFileType(field.def.type) }"
          >
            <!-- File/Image Input with Preview -->
            <template v-if="isFileType(field.def.type)">
              <div
                class="file-drop-zone"
                :class="{ 'has-file': inputValues[field.key], 'dragging': isDragging === field.key }"
                @click="triggerFileInput(field.key)"
                @dragover.prevent="isDragging = field.key"
                @dragleave="isDragging = null"
                @drop.prevent="handleFileDrop(field.key, $event)"
              >
                <!-- Preview if has file -->
                <template v-if="inputValues[field.key]">
                  <div class="file-preview">
                    <!-- Image Preview -->
                    <img
                      v-if="isImageFile(inputValues[field.key])"
                      :src="filePreviewUrls[field.key]"
                      class="image-preview"
                      :alt="$t('alt.preview')"
                    />
                    <!-- Non-image file -->
                    <div v-else class="file-icon-preview">
                      <FileText :size="48" />
                      <span class="file-name">{{ inputValues[field.key].name }}</span>
                      <span class="file-size">{{ formatFileSize(inputValues[field.key].size) }}</span>
                    </div>
                  </div>
                  <button class="remove-file" @click.stop="removeFile(field.key)">
                    <X :size="16" />
                  </button>
                </template>

                <!-- Empty state -->
                <template v-else>
                  <div class="drop-content">
                    <component :is="getFileIcon(field.def)" :size="40" />
                    <span class="drop-text">{{ field.def.label || field.key }}</span>
                    <span class="drop-hint">{{ $t('simpleToolView.dropOrClick') }}</span>
                  </div>
                </template>
              </div>
              <input
                :ref="el => fileInputRefs[field.key] = el"
                type="file"
                class="hidden-input"
                :accept="getAcceptTypes(field.def)"
                @change="handleFileSelect(field.key, $event)"
              />
            </template>

            <!-- Text Input -->
            <template v-else-if="field.def.type === 'string'">
              <label class="input-label">{{ field.def.label || field.key }}</label>
              <AppInput
                v-model="inputValues[field.key]"
                :placeholder="field.def.placeholder || field.def.label"
              />
            </template>

            <!-- Textarea -->
            <template v-else-if="field.def.type === 'text'">
              <label class="input-label">{{ field.def.label || field.key }}</label>
              <AppTextarea
                v-model="inputValues[field.key]"
                :placeholder="field.def.placeholder"
                :rows="4"
              />
            </template>

            <!-- Number -->
            <template v-else-if="field.def.type === 'number'">
              <label class="input-label">{{ field.def.label || field.key }}</label>
              <input
                v-model.number="inputValues[field.key]"
                type="number"
                class="text-input"
                :min="field.def.min"
                :max="field.def.max"
                :step="field.def.step || 1"
              />
            </template>

            <!-- Select -->
            <template v-else-if="field.def.type === 'select'">
              <label class="input-label">{{ field.def.label || field.key }}</label>
              <AppSelect
                v-model="inputValues[field.key]"
                :placeholder="$t('simpleToolView.selectOption')"
                :options="field.def.options"
              />
            </template>

            <!-- Boolean Toggle -->
            <template v-else-if="field.def.type === 'boolean'">
              <label class="toggle-label" @click="inputValues[field.key] = !inputValues[field.key]">
                <span class="toggle-text">{{ field.def.label || field.key }}</span>
                <div class="toggle-switch" :class="{ active: inputValues[field.key] }">
                  <div class="toggle-knob"></div>
                </div>
              </label>
            </template>
          </div>
        </div>
      </div>

      <!-- PROCESS SECTION -->
      <ProcessButton
        :is-executing="isExecuting"
        :can-run="canRun"
        :steps="steps"
        :current-step-index="currentStepIndex"
        @execute="execute"
      />

      <!-- OUTPUT SECTION -->
      <OutputDisplay
        :is-executing="isExecuting"
        :execution-result="executionResult"
        :error-message="errorMessage"
        @retry="execute"
        @download="downloadResult"
        @copy="copyResult"
        @copy-image="copyToClipboard"
        @download-as-file="downloadAsFile"
      />
    </div>

    <!-- Expandable Flow Details -->
    <FlowSteps
      v-if="showFlowDetails"
      :steps="steps"
      :current-step-index="currentStepIndex"
    />
  </div>
</template>

<script setup>
import { reactive, computed, watch } from 'vue'
import { Upload, FileText, Image, File, X } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'
import SchemaParamsRenderer from '@/components/templateBuilder/SchemaParamsRenderer.vue'
import { getParamsSchema } from '@/composables/toolStorage/toolHelpers'
import ToolHeader from './ToolHeader.vue'
import ProcessButton from './ProcessButton.vue'
import OutputDisplay from './OutputDisplay.vue'
import FlowSteps from './FlowSteps.vue'
import { useFileInput } from '@/composables/useFileInput'
import { useToolExecution } from '@/composables/useToolExecution'
import { useResultActions } from '@/composables/useResultActions'

const props = defineProps({
  tool: {
    type: Object,
    required: true
  },
  showAdvancedToggle: {
    type: Boolean,
    default: true
  },
  showFlowDetails: {
    type: Boolean,
    default: true
  },
  useAutoForm: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['toggle-advanced', 'execution-complete', 'execution-error'])

// State
const inputValues = reactive({})

// ===== Composables =====
const {
  filePreviewUrls,
  fileInputRefs,
  isDragging,
  isImageFile,
  isFileType,
  formatFileSize,
  getAcceptTypes,
  triggerFileInput,
  handleFileSelect: handleFileSelectBase,
  handleFileDrop: handleFileDropBase,
  removeFile: removeFileBase
} = useFileInput()

const {
  isExecuting,
  currentStepIndex,
  executionResult,
  errorMessage,
  execute: executeBase
} = useToolExecution({
  onComplete: (result) => emit('execution-complete', result),
  onError: (e) => emit('execution-error', e)
})

const {
  downloadResult: downloadResultBase,
  copyResult: copyResultBase,
  copyImageToClipboard,
  downloadAsFile: downloadAsFileBase
} = useResultActions({
  getResult: () => executionResult.value
})

// Use shared getParamsSchema — handles both flat and {type:"object",properties:{}} formats
const paramsSchema = computed(() => getParamsSchema(props.tool))

// Computed — extract flat field definitions from tool inputs or normalized schema
const inputFields = computed(() => {
  const raw = props.tool?.inputs || props.tool?.meta?.paramsSchema || {}
  // Handle {type:"object", properties:{...}} normalized format
  const fields = (raw.type === 'object' && raw.properties) ? raw.properties : raw
  if (!fields || typeof fields !== 'object') return []
  return Object.entries(fields)
    .filter(([key]) => key !== 'type' && key !== 'required')
    .map(([key, def]) => ({ key, def: typeof def === 'object' ? def : { type: 'string' } }))
})

const steps = computed(() => props.tool?.flow?.steps || [])

const canRun = computed(() => {
  for (const field of inputFields.value) {
    if (field.def.required && !hasValue(field.key)) {
      return false
    }
  }
  return true
})

// ===== Methods =====
function hasValue(key) {
  const val = inputValues[key]
  if (val === null || val === undefined || val === '') return false
  return true
}

function getFileIcon(def) {
  if (def.type === 'image' || def.accept?.includes('image')) return Image
  return File
}

// Wrapper functions for composable methods (pass inputValues)
function handleFileSelect(key, event) {
  handleFileSelectBase(key, event, inputValues)
}

function handleFileDrop(key, event) {
  handleFileDropBase(key, event, inputValues)
}

function removeFile(key) {
  removeFileBase(key, inputValues)
}

async function execute() {
  if (!canRun.value) return
  await executeBase(props.tool, steps.value, inputValues)
}

function downloadResult() {
  downloadResultBase()
}

function copyResult() {
  copyResultBase()
}

function copyToClipboard() {
  copyImageToClipboard()
}

function downloadAsFile() {
  downloadAsFileBase()
}

// Initialize input values from inputFields (handles both flat and normalized formats)
watch(() => props.tool, () => {
  for (const { key, def } of inputFields.value) {
    if (inputValues[key] === undefined) {
      inputValues[key] = def.default ?? (def.type === 'boolean' ? false : '')
    }
  }
}, { immediate: true })
</script>

<style scoped>
.simple-tool-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

/* Flow Layout */
.tool-flow {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 24px;
  align-items: start;
}

@media (max-width: 900px) {
  .tool-flow {
    grid-template-columns: 1fr;
  }
}

/* Sections */
.flow-section {
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

/* Schema Form Wrapper */
.auto-form-wrapper {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 20px;
}

.auto-form-wrapper :deep(.form-field) {
  margin-bottom: 16px;
}

.auto-form-wrapper :deep(.form-field:last-child) {
  margin-bottom: 0;
}

/* Input Cards */
.input-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.input-card {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s;
}

.input-card.has-value {
  border-color: #3b82f6;
}

.input-card.is-file {
  padding: 0;
  overflow: hidden;
}

/* File Drop Zone */
.file-drop-zone {
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
}

.file-drop-zone:hover,
.file-drop-zone.dragging {
  background: rgba(59, 130, 246, 0.1);
}

.file-drop-zone.has-file {
  background: #0f172a;
}

.drop-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #64748b;
}

.drop-text {
  font-size: 14px;
  font-weight: 500;
  color: #94a3b8;
}

.drop-hint {
  font-size: 12px;
}

.file-preview {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-preview {
  max-width: 100%;
  max-height: 200px;
  object-fit: contain;
  border-radius: 8px;
}

.file-icon-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px;
  color: #64748b;
}

.file-name {
  font-size: 13px;
  color: #f1f5f9;
  word-break: break-all;
  text-align: center;
}

.file-size {
  font-size: 12px;
  color: #64748b;
}

.remove-file {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: rgba(239, 68, 68, 0.9);
  color: white;
  cursor: pointer;
}

.hidden-input {
  display: none;
}

/* Text Inputs */
.input-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #94a3b8;
  margin-bottom: 8px;
}

.text-input,
.textarea-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #334155;
  border-radius: 8px;
  background: #0f172a;
  color: #f1f5f9;
  font-size: 14px;
  transition: border-color 0.2s;
}

.text-input:focus,
.textarea-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.textarea-input {
  resize: vertical;
  min-height: 80px;
}

/* Toggle */
.toggle-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}

.toggle-text {
  font-size: 14px;
  color: #f1f5f9;
}

.toggle-switch {
  width: 48px;
  height: 26px;
  background: #334155;
  border-radius: 13px;
  position: relative;
  transition: background 0.2s;
}

.toggle-switch.active {
  background: #3b82f6;
}

.toggle-knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s;
}

.toggle-switch.active .toggle-knob {
  transform: translateX(22px);
}
</style>

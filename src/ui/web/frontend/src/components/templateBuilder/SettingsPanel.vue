<template>
  <div
    :class="['settings-panel', show ? 'translate-x-0' : 'translate-x-full']"
  >
    <div class="panel-header">
      <h3 class="header-title">
        <Settings :size="18" class="text-primary-600" />
        {{ $t('templateBuilder.settings.title', 'Settings') }}
      </h3>
      <button
        @click="$emit('close')"
        class="close-btn"
        :title="$t('common.close')"
      >
        <X :size="18" />
      </button>
    </div>

    <div class="panel-body custom-scrollbar">
      <!-- Template Info Section -->
      <div class="settings-section">
        <h4 class="section-title">
          <FileText :size="16" />
          {{ $t('templateBuilder.settings.templateInfo', 'Template Info') }}
        </h4>

        <div class="input-group">
          <label class="input-label">{{ $t('templateBuilder.header.nameLabel', 'Name') }}</label>
          <AppInput
            :modelValue="templateName"
            @update:modelValue="$emit('update:templateName', $event)"
            :placeholder="$t('templateBuilder.toolbar.templateNamePlaceholder', 'Template Name')"
            size="sm"
          />
        </div>

        <div class="input-group">
          <label class="input-label">{{ $t('templateBuilder.header.idLabel', 'ID') }}</label>
          <AppInput
            :modelValue="templateId"
            @update:modelValue="!existingTemplateId && $emit('update:templateId', $event)"
            :placeholder="$t('templateBuilder.toolbar.templateIdPlaceholder', 'template-id')"
            :readonly="!!existingTemplateId"
            size="sm"
          />
          <p v-if="existingTemplateId" class="input-hint">
            {{ $t('templateBuilder.settings.idReadonly', 'ID cannot be changed after creation') }}
          </p>
        </div>

        <div class="input-group">
          <label class="input-label">{{ $t('templateBuilder.settings.description', 'Description') }}</label>
          <AppTextarea
            :modelValue="templateDescription"
            @update:modelValue="$emit('update:templateDescription', $event)"
            :placeholder="$t('templateBuilder.settings.descriptionPlaceholder', 'Describe what this template does...')"
            :rows="3"
            size="sm"
          />
        </div>
      </div>

      <!-- Import / Export Section -->
      <div class="settings-section">
        <h4 class="section-title">
          <FileCode :size="16" />
          {{ $t('templateBuilder.settings.importExport', 'Import / Export') }}
        </h4>
        <p class="section-description">
          {{ $t('templateBuilder.settings.importExportDesc', 'Import or export your workflow as YAML file') }}
        </p>

        <div class="action-buttons">
          <button @click="$emit('import')" class="action-btn import">
            <Upload :size="18" />
            <div class="btn-content">
              <span class="btn-label">{{ $t('templateBuilder.settings.importYaml', 'Import YAML') }}</span>
              <span class="btn-hint">{{ $t('templateBuilder.settings.importHint', 'Load workflow from .yaml file') }}</span>
            </div>
          </button>

          <button @click="$emit('export')" class="action-btn export">
            <Download :size="18" />
            <div class="btn-content">
              <span class="btn-label">{{ $t('templateBuilder.settings.exportYaml', 'Export YAML') }}</span>
              <span class="btn-hint">{{ $t('templateBuilder.settings.exportHint', 'Download workflow as .yaml file') }}</span>
            </div>
          </button>
        </div>
      </div>

      <!-- Execution Settings Section -->
      <div class="settings-section">
        <h4 class="section-title">
          <Camera :size="16" />
          {{ $t('templateBuilder.settings.executionSettings', 'Execution Settings') }}
        </h4>

        <div class="input-group">
          <label class="input-label">{{ $t('templateBuilder.settings.screenshotMode', 'Screenshot Mode') }}</label>
          <AppSelect
            :modelValue="screenshotMode"
            @update:modelValue="$emit('update:screenshotMode', $event)"
            :options="[
              { value: 'off', label: $t('templateBuilder.settings.screenshotOff', 'Off - No screenshots') },
              { value: 'on_error', label: $t('templateBuilder.settings.screenshotOnError', 'On Error - Only capture when step fails') },
              { value: 'all', label: $t('templateBuilder.settings.screenshotAll', 'All - Capture every browser step') }
            ]"
          />
          <p class="input-hint">
            {{ $t('templateBuilder.settings.screenshotHint', 'Screenshots help debug browser automation issues') }}
          </p>
        </div>
      </div>

      <!-- Error Handling Section -->
      <div class="settings-section">
        <h4 class="section-title error-title">
          <AlertTriangle :size="16" />
          {{ $t('errorWorkflow.title', 'Error Handling') }}
        </h4>
        <p class="section-description">
          {{ $t('errorWorkflow.description', 'Configure what happens when this workflow fails') }}
        </p>

        <div class="input-group">
          <label class="input-label">{{ $t('errorWorkflow.onFailure', 'On Workflow Failure') }}</label>
          <AppSelect
            :modelValue="errorHandling.onFailure"
            @update:modelValue="updateErrorSetting('onFailure', $event)"
            :options="[
              { value: 'none', label: $t('errorWorkflow.doNothing', 'Do nothing') },
              { value: 'run_workflow', label: $t('errorWorkflow.runWorkflow', 'Run error workflow') }
            ]"
          />
        </div>

        <!-- Conditional: Error Workflow Selection -->
        <div v-if="errorHandling.onFailure === 'run_workflow'" class="error-workflow-wrapper">
          <ErrorWorkflowSelector
            :model-value="errorHandling.errorWorkflowId || ''"
            :current-workflow-id="templateId"
            @update:model-value="updateErrorSetting('errorWorkflowId', $event || null)"
          />
        </div>

        <!-- Pass Error Context Checkbox -->
        <div v-if="errorHandling.onFailure === 'run_workflow'" class="checkbox-group">
          <label class="checkbox-label">
            <input
              type="checkbox"
              :checked="errorHandling.passErrorContext"
              @change="updateErrorSetting('passErrorContext', $event.target.checked)"
            />
            <span>{{ $t('errorWorkflow.passContext', 'Pass error context to error workflow') }}</span>
          </label>
          <p class="input-hint">
            {{ $t('errorWorkflow.passContextHint', 'Includes error message, category, and source workflow data') }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Settings, X, FileCode, FileText, Upload, Download, AlertTriangle, Camera } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'
import ErrorWorkflowSelector from '@/components/workflow/ErrorWorkflowSelector.vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  templateName: {
    type: String,
    default: ''
  },
  templateId: {
    type: String,
    default: ''
  },
  templateDescription: {
    type: String,
    default: ''
  },
  existingTemplateId: {
    type: String,
    default: null
  },
  errorHandling: {
    type: Object,
    default: () => ({
      onFailure: 'none',
      errorWorkflowId: null,
      passErrorContext: true
    })
  },
  availableWorkflows: {
    type: Array,
    default: () => []
  },
  screenshotMode: {
    type: String,
    default: 'on_error'
  }
})

const emit = defineEmits([
  'close',
  'import',
  'export',
  'update:templateName',
  'update:templateId',
  'update:templateDescription',
  'update:errorHandling',
  'update:screenshotMode'
])

function updateErrorSetting(key, value) {
  emit('update:errorHandling', {
    ...props.errorHandling,
    [key]: value
  })
}
</script>

<style scoped>
.settings-panel {
  position: fixed;
  top: 0;
  right: 0;
  height: 100%;
  width: 360px;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  border-left: 1px solid #334155;
  box-shadow: -10px 0 40px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s ease-in-out;
  z-index: 50;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #334155;
  background: rgba(30, 41, 59, 0.8);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.header-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #f1f5f9;
  display: flex;
  align-items: center;
  gap: 8px;
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: none;
  background: rgba(71, 85, 105, 0.3);
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.panel-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

/* Settings Section */
.settings-section {
  margin-bottom: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
  margin: 0 0 8px 0;
}

.section-description {
  font-size: 12px;
  color: #64748b;
  margin: 0 0 16px 0;
  line-height: 1.5;
}

/* Input Fields */
.input-group {
  margin-bottom: 16px;
}

.input-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.input-field {
  width: 100%;
  padding: 10px 12px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid #475569;
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 14px;
  transition: all 0.2s;
}

.input-field:focus {
  outline: none;
  border-color: #8B5CF6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.input-field::placeholder {
  color: #475569;
}

.input-field.mono {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 13px;
}

.input-field.readonly {
  opacity: 0.7;
  cursor: not-allowed;
  background: rgba(15, 23, 42, 0.5);
}

.input-field.textarea {
  resize: vertical;
  min-height: 80px;
}

.input-hint {
  font-size: 11px;
  color: #64748b;
  margin-top: 4px;
}

/* Checkbox Group */
.checkbox-group {
  margin-bottom: 16px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 10px 12px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid #475569;
  border-radius: 8px;
  transition: all 0.2s;
}

.checkbox-label:hover {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.3);
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #EF4444;
  cursor: pointer;
}

.checkbox-label span {
  font-size: 13px;
  color: #e2e8f0;
}

/* Error Title */
.section-title.error-title {
  color: #f87171;
}

.section-title.error-title svg {
  color: #EF4444;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-btn {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  width: 100%;
  padding: 14px 16px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid #475569;
  border-radius: 10px;
  color: #e2e8f0;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.action-btn:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.4);
}

.action-btn svg {
  flex-shrink: 0;
  margin-top: 2px;
  color: #94a3b8;
  transition: color 0.2s;
}

.action-btn:hover svg {
  color: #a78bfa;
}

.btn-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.btn-label {
  font-size: 14px;
  font-weight: 500;
}

.btn-hint {
  font-size: 12px;
  color: #64748b;
}

.action-btn.import:hover {
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.4);
}

.action-btn.import:hover svg {
  color: #22c55e;
}

.action-btn.export:hover {
  background: rgba(6, 182, 212, 0.1);
  border-color: rgba(6, 182, 212, 0.4);
}

.action-btn.export:hover svg {
  color: #06b6d4;
}

/* Custom Scrollbar */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}
</style>

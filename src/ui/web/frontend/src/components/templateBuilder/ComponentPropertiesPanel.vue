<template>
  <div :class="['properties-panel', show ? 'translate-x-0' : 'translate-x-full']">
    <PanelHeader @close="$emit('close')" />
    <div v-if="component" class="panel-body custom-scrollbar">
      <PropertyField :label="$t('templateBuilder.properties.componentId') + ' *'" :icon="Hash"
        :model-value="component.id" @update:model-value="updateField('id', $event)" />
      <PropertyField :label="$t('templateBuilder.properties.labelText')" :icon="Tag"
        :model-value="component.label" @update:model-value="updateField('label', $event)" expandable>
        <template #expanded>
          <OptionInput :label="$t('templateBuilder.properties.placeholder')"
            :model-value="component.placeholder" @update:model-value="updateField('placeholder', $event)" />
          <OptionInput :label="$t('templateBuilder.properties.helpText')"
            :model-value="component.helpText" @update:model-value="updateField('helpText', $event)" />
        </template>
      </PropertyField>
      <PropertyField v-if="component.type !== 'button'" :label="$t('templateBuilder.properties.defaultValue')"
        :icon="FileText" :model-value="component.default" @update:model-value="updateField('default', $event)" expandable>
        <template #expanded>
          <OptionCheckbox :label="$t('templateBuilder.properties.disabled')"
            :model-value="component.disabled" @update:model-value="updateField('disabled', $event)" />
          <OptionCheckbox :label="$t('templateBuilder.properties.readonly')"
            :model-value="component.readonly" @update:model-value="updateField('readonly', $event)" />
        </template>
      </PropertyField>
      <PropertyField v-if="component.type === 'input'" :label="$t('templateBuilder.properties.inputType')"
        :icon="Type" input-type="select" :model-value="component.inputType"
        @update:model-value="updateField('inputType', $event)" :options="inputTypeOptions" />
      <PropertyField v-if="component.type === 'select'" :label="$t('templateBuilder.properties.optionsLabel')"
        :icon="List" input-type="textarea"
        :model-value="computedSelectOptionsText"
        @update:model-value="handleSelectOptionsInput"
        placeholder="value:label (one per line)"
        expandable>
        <template #expanded>
          <OptionCheckbox :label="$t('templateBuilder.properties.allowMultiple')"
            :model-value="component.multiple" @update:model-value="updateField('multiple', $event)" />
          <!-- Import from Snapshot hints -->
          <div v-if="hintSelects.length" class="import-hints-section">
            <label class="import-label">{{ $t('templateBuilder.importFromPage', 'Import from page') }}</label>
            <div class="import-list">
              <button
                v-for="(sel, idx) in hintSelects" :key="idx"
                class="import-btn" @click="importSelectOptions(sel)"
              >
                <Download :size="12" />
                <span class="import-btn-label">{{ sel.name || sel.selector }}</span>
                <span class="import-btn-count">{{ (sel.options || []).length }}</span>
              </button>
            </div>
          </div>
        </template>
      </PropertyField>
      <PropertyField v-if="component.type === 'radio'" :label="$t('templateBuilder.properties.optionsLabel')"
        :icon="List" input-type="textarea" :model-value="radioOptionsText"
        @update:model-value="emit('update:radio-options', $event)" expandable>
        <template #expanded>
          <OptionInput :label="$t('templateBuilder.properties.radioLayout')" input-type="select"
            :model-value="component.layout" @update:model-value="updateField('layout', $event)" :options="layoutOptions" />
        </template>
      </PropertyField>
      <PropertyField v-if="component.type === 'button'" :label="$t('templateBuilder.properties.buttonText')"
        :icon="Type" :model-value="component.text" @update:model-value="updateField('text', $event)" expandable>
        <template #expanded>
          <OptionInput :label="$t('templateBuilder.properties.buttonType')" input-type="select"
            :model-value="component.buttonType" @update:model-value="updateField('buttonType', $event)" :options="buttonTypeOptions" />
          <OptionInput :label="$t('templateBuilder.properties.buttonStyle')" input-type="select"
            :model-value="component.variant" @update:model-value="updateField('variant', $event)" :options="buttonStyleOptions" />
        </template>
      </PropertyField>
      <ValidationSection :enabled="validationEnabled" :expanded="expandedSections.validation"
        :validation="component.validation" :show-length-fields="component.type === 'input'"
        @toggle="expandedSections.validation = !expandedSections.validation"
        @update:enabled="emit('update:validation-enabled', $event)" @update:field="updateValidation" />
      <ConditionalSection :model-value="component.show_if" @update:model-value="updateField('show_if', $event)" />
    </div>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'
import { Hash, Tag, FileText, Type, List, Download } from 'lucide-vue-next'
import PropertyField from './PropertyField.vue'
import OptionCheckbox from './OptionCheckbox.vue'
import OptionInput from './OptionInput.vue'
import { PanelHeader, ValidationSection, ConditionalSection, usePropertyOptions } from './properties'
import { useNodeOutputStore } from '@/stores/execution'

const { inputTypeOptions, layoutOptions, buttonTypeOptions, buttonStyleOptions } = usePropertyOptions()
const nodeOutputStore = useNodeOutputStore()

const props = defineProps({
  show: { type: Boolean, default: false },
  component: { type: Object, default: null },
  validationEnabled: { type: Boolean, default: false },
  selectOptionsText: { type: String, default: '' },
  radioOptionsText: { type: String, default: '' }
})
const emit = defineEmits(['close', 'update:validation-enabled', 'update:select-options', 'update:radio-options'])
const expandedSections = reactive({ validation: false })
const updateField = (field, value) => { if (props.component) props.component[field] = value }

// Directly compute options text from component.options (no emit chain needed)
const computedSelectOptionsText = computed(() => {
  const options = props.component?.options || []
  return options.map(opt => {
    if (typeof opt === 'string') return opt
    const v = opt.value || ''
    const l = opt.label || ''
    return v === l ? v : (v + ':' + l)
  }).join('\n')
})

function handleSelectOptionsInput(text) {
  if (!props.component) return
  const lines = (text || '').split('\n').filter(l => l.trim())
  props.component.options = lines.map(line => {
    const idx = line.indexOf(':')
    if (idx > 0) {
      return { value: line.substring(0, idx), label: line.substring(idx + 1) }
    }
    return { value: line.trim(), label: line.trim() }
  })
}
const updateValidation = (field, value) => { if (props.component?.validation) props.component.validation[field] = value }

// Collect all selects from any node output that has hint data
const hintSelects = computed(() => {
  const results = []
  const outputs = nodeOutputStore.nodeOutputs || {}
  for (const nodeId in outputs) {
    const output = outputs[nodeId]?.output || outputs[nodeId]
    if (!output || typeof output !== 'object') continue
    const selects = output.selects
    if (Array.isArray(selects)) {
      for (const sel of selects) {
        if (sel.options && sel.options.length > 0) {
          results.push(sel)
        }
      }
    }
  }
  return results
})

function importSelectOptions(sel) {
  if (!props.component) return
  // Directly update component options array
  const options = (sel.options || [])
    .filter(opt => opt.value || opt.label)
    .map(opt => ({
      value: opt.value || opt.label || '',
      label: opt.label || opt.value || ''
    }))
  props.component.options = options
  // Also emit text update so the textarea syncs
  const lines = options.map(o => o.value === o.label ? o.value : (o.value + ':' + o.label))
  emit('update:select-options', lines.join('\n'))
}
</script>

<style scoped>
.properties-panel {
  position: fixed; top: 0; right: 0; height: 100%; width: 400px;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  border-left: 1px solid #334155; box-shadow: -10px 0 40px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s ease-in-out; z-index: 50; display: flex; flex-direction: column;
}
.panel-body { flex: 1; padding: 20px; overflow-y: auto; }
.import-hints-section { margin-top: 14px; padding-top: 14px; border-top: 1px solid #334155; }
.import-label { display: block; font-size: 11px; font-weight: 600; color: #64748b; margin-bottom: 8px; }
.import-list { display: flex; flex-direction: column; gap: 4px; }
.import-btn {
  display: flex; align-items: center; gap: 6px; width: 100%;
  padding: 8px 10px; background: rgba(139, 92, 246, 0.08); border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 6px; color: #a78bfa; font-size: 12px; cursor: pointer; transition: all 0.15s; text-align: left;
}
.import-btn:hover { background: rgba(139, 92, 246, 0.15); border-color: rgba(139, 92, 246, 0.4); }
.import-btn-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.import-btn-count {
  flex-shrink: 0; padding: 1px 6px; background: rgba(139, 92, 246, 0.2);
  border-radius: 4px; font-size: 10px; font-weight: 600;
}
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #475569; border-radius: 3px; }
</style>

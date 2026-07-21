<template>
  <div class="schema-params-renderer" :class="{ compact }">
    <!-- Loading state -->
    <div v-if="loading" class="loading-state">
      <Loader2 :size="16" class="spin" />
      <span>{{ t('common.loading') }}</span>
    </div>

    <!-- Schema-driven form (has schema) -->
    <div v-else-if="schema && fields.length > 0" class="params-form">
      <!-- visibilityMode: null → original basic/expert split -->
      <template v-if="!visibilityMode">
        <!-- Basic fields (non-expert) -->
        <template v-for="field in basicFields" :key="field.key">
          <div class="param-field">
            <label class="param-label">
              <span class="label-text">{{ getFieldLabel(field) }}</span>
              <span v-if="field.required" class="required-mark">*</span>
              <span v-if="getFieldDescription(field)" class="label-hint" :title="getFieldDescription(field)">
                <HelpCircle :size="12" />
              </span>
            </label>

            <SchemaField
              :field="field"
              :value="localParams[field.key]"
              :readonly="readOnly"
              :ui-input-fields="uiInputFields"
              :previous-steps="previousSteps"
              :all-params="localParams"
              @update:value="updateParam(field.key, $event)"
              @auto-switch-method="onAutoSwitchMethod(field, $event)"
            />

            <p v-if="errors[field.key]" class="field-error">{{ errors[field.key] }}</p>

            <!-- Dynamic [[var]] input fields -->
            <div v-for="varName in getVarsForField(field.key)" :key="`${field.key}__${varName}`" class="dynamic-var-field">
              <label class="param-label">
                <span class="label-text dynamic-var-label">[[{{ varName }}]]</span>
              </label>
              <ValueSourceSelector
                :modelValue="localParams._tvars?.[varName] ?? ''"
                inputType="text"
                :placeholder="varName"
                :paramKey="`__var_${varName}`"
                :uiInputFields="uiInputFields"
                :previousSteps="previousSteps"
                :readonly="readOnly"
                @update:modelValue="updateVar(varName, $event)"
              />
            </div>
          </div>
        </template>

        <!-- Expert/Advanced fields (collapsible) -->
        <div v-if="expertFields.length > 0" class="expert-section">
          <button
            class="expert-toggle"
            @click="showExpert = !showExpert"
            type="button"
          >
            <ChevronRight :size="14" :class="{ rotated: showExpert }" />
            <span>{{ t('templateBuilder.schemaParams.advancedOptions') }}</span>
            <span class="expert-count">{{ expertFields.length }}</span>
          </button>

          <Transition name="slide">
            <div v-if="showExpert" class="expert-fields">
              <template v-for="field in expertFields" :key="field.key">
                <div class="param-field">
                  <label class="param-label">
                    <span class="label-text">{{ getFieldLabel(field) }}</span>
                    <span v-if="field.required" class="required-mark">*</span>
                    <span v-if="getFieldDescription(field)" class="label-hint" :title="getFieldDescription(field)">
                      <HelpCircle :size="12" />
                    </span>
                  </label>

                  <SchemaField
                    :field="field"
                    :value="localParams[field.key]"
                    :readonly="readOnly"
                    :ui-input-fields="uiInputFields"
                    :previous-steps="previousSteps"
                    @update:value="updateParam(field.key, $event)"
                    @auto-switch-method="onAutoSwitchMethod(field, $event)"
                  />

                  <p v-if="errors[field.key]" class="field-error">{{ errors[field.key] }}</p>

                  <!-- Dynamic [[var]] input fields -->
                  <div v-for="varName in getVarsForField(field.key)" :key="`${field.key}__${varName}`" class="dynamic-var-field">
                    <label class="param-label">
                      <span class="label-text dynamic-var-label">[[{{ varName }}]]</span>
                    </label>
                    <ValueSourceSelector
                      :modelValue="localParams._tvars?.[varName] ?? ''"
                      inputType="text"
                      :placeholder="varName"
                      :paramKey="`__var_${varName}`"
                      :uiInputFields="uiInputFields"
                      :previousSteps="previousSteps"
                      :readonly="readOnly"
                      @update:modelValue="updateVar(varName, $event)"
                    />
                  </div>
                </div>
              </template>
            </div>
          </Transition>
        </div>
      </template>

      <!-- visibilityMode: 'simple' | 'advanced' | 'all' → grouped layout -->
      <template v-else>
        <div v-for="group in groupedFields" :key="group.name" class="field-group">
          <!-- Group Header (only shown when multiple groups) -->
          <button
            v-if="hasMultipleGroups"
            type="button"
            class="group-header"
            @click="toggleGroup(group.name)"
          >
            <ChevronRight
              :size="14"
              class="group-chevron"
              :class="{ 'is-expanded': !group.collapsed }"
            />
            <span class="group-title">{{ t(`form.group.${group.name}`) }}</span>
            <span class="group-count">({{ group.fields.length }})</span>
          </button>

          <!-- Group Content -->
          <div v-show="!hasMultipleGroups || !group.collapsed" class="group-content">
            <template v-for="field in group.fields" :key="field.key">
              <div class="param-field">
                <label class="param-label">
                  <span class="label-text">{{ getFieldLabel(field) }}</span>
                  <span v-if="field.required" class="required-mark">*</span>
                  <span v-if="getFieldDescription(field)" class="label-hint" :title="getFieldDescription(field)">
                    <HelpCircle :size="12" />
                  </span>
                </label>

                <SchemaField
                  :field="field"
                  :value="localParams[field.key]"
                  :readonly="readOnly"
                  :ui-input-fields="uiInputFields"
                  :previous-steps="previousSteps"
                  :all-params="localParams"
                  @update:value="updateParam(field.key, $event)"
                  @auto-switch-method="onAutoSwitchMethod(field, $event)"
                />

                <p v-if="errors[field.key]" class="field-error">{{ errors[field.key] }}</p>

                <!-- Dynamic [[var]] input fields -->
                <div v-for="varName in getVarsForField(field.key)" :key="`${field.key}__${varName}`" class="dynamic-var-field">
                  <label class="param-label">
                    <span class="label-text dynamic-var-label">[[{{ varName }}]]</span>
                  </label>
                  <ValueSourceSelector
                    :modelValue="localParams._tvars?.[varName] ?? ''"
                    inputType="text"
                    :placeholder="varName"
                    :paramKey="`__var_${varName}`"
                    :uiInputFields="uiInputFields"
                    :previousSteps="previousSteps"
                    :readonly="readOnly"
                    @update:modelValue="updateVar(varName, $event)"
                  />
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- Show Advanced Toggle (simple mode only) -->
        <button
          v-if="showExpertToggleButton"
          type="button"
          class="show-advanced"
          @click="showExpert = true"
        >
          <ChevronDown :size="14" />
          {{ t('templateBuilder.schemaParams.advancedOptions') }}
        </button>

        <!-- Hide Advanced (when shown in simple mode) -->
        <button
          v-if="visibilityMode === 'simple' && showExpert && hasExpertFields"
          type="button"
          class="show-advanced"
          @click="showExpert = false"
        >
          <ChevronDown :size="14" class="rotate-180" />
          {{ t('templateBuilder.schemaParams.hideAdvanced') }}
        </button>
      </template>

    </div>

    <!-- Generic mode: No schema but has params (fallback mode) -->
    <div v-else-if="hasParams" class="params-form generic-mode">
      <div
        v-for="(value, key) in visibleParams"
        :key="key"
        class="param-field"
      >
        <label class="param-label">
          <span class="label-text">{{ formatParamLabel(key) }}</span>
        </label>

        <ValueSourceSelector
          :modelValue="localParams[key]"
          :inputType="inferInputType(value)"
          :placeholder="t('common.enterValue', { field: formatParamLabel(key) })"
          :paramKey="key"
          :uiInputFields="uiInputFields"
          :previousSteps="previousSteps"
          :readonly="readOnly"
          @update:modelValue="updateParam(key, $event)"
        />
      </div>
    </div>

    <!-- No schema and no params -->
    <div v-else class="empty-state">
      <Info :size="16" />
      <span>{{ t('templateBuilder.schemaParams.noSchema') }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Loader2, Info, HelpCircle, ChevronRight, ChevronDown } from 'lucide-vue-next'
import { parseParamsSchema } from '@/composables/paramRenderer'
import SchemaField from './SchemaField.vue'
import ValueSourceSelector from '@/components/ValueSourceSelector.vue'
import { formatParamLabel } from '@/utils/format'

const { t } = useI18n()

// Group order for rendering
const GROUP_ORDER = ['basic', 'connection', 'options', 'advanced']

const props = defineProps({
  schema: {
    type: Object,
    default: null
  },
  params: {
    type: Object,
    default: () => ({})
  },
  modelValue: {
    type: Object,
    default: null
  },
  moduleId: {
    type: String,
    default: ''
  },
  readOnly: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  uiInputFields: {
    type: Array,
    default: () => []
  },
  previousSteps: {
    type: Array,
    default: () => []
  },
  compact: {
    type: Boolean,
    default: false
  },
  visibilityMode: {
    type: String,
    default: null,
    validator: v => v === null || ['simple', 'advanced', 'all'].includes(v)
  },
  errors: {
    type: Object,
    default: () => ({})
  },
  allowExpertToggle: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:params', 'update:modelValue'])

// Local state
const showExpert = ref(false)
const collapsedGroups = reactive({})
// Parse schema into field definitions (with moduleId for i18n)
// Defined BEFORE localParams so we can use defaults from schema
const fields = computed(() => {
  if (!props.schema) return []
  return parseParamsSchema(props.schema, props.moduleId)
})

// Build a map of schema defaults for all fields.
// Used to fill localParams so that showIf conditions and element picker
// value_key_from can read sibling defaults even when the user never touched them.
function _schemaDefaults() {
  const defaults = {}
  for (const f of fields.value) {
    if (f.default !== undefined) {
      defaults[f.key] = f.default
    }
  }
  return defaults
}

// Merge schema defaults under user params (defaults don't overwrite explicit values)
function _mergeDefaults(params) {
  const defaults = _schemaDefaults()
  return { ...defaults, ...params }
}

const localParams = ref(_mergeDefaults(props.modelValue || props.params))

// Watch for external params/modelValue changes
// Use JSON key fingerprint instead of deep watch to avoid O(n) traversal on every keystroke
function _paramKeys(obj) {
  if (!obj) return ''
  return Object.keys(obj).sort().join(',') + '|' + Object.values(obj).map(v => typeof v === 'object' ? JSON.stringify(v) : String(v)).join(',')
}

watch(() => props.params ? _paramKeys(props.params) : null, () => {
  if (!props.modelValue && props.params) {
    localParams.value = _mergeDefaults(props.params)
  }
})

watch(() => props.modelValue ? _paramKeys(props.modelValue) : null, () => {
  if (props.modelValue) {
    localParams.value = _mergeDefaults(props.modelValue)
  }
})

// Detect [[varName]] in a field's current value → return list of variable names
const BRACKET_VAR_RE = /\[\[(\w+)\]\]/g
function getVarsForField(fieldKey) {
  const val = localParams.value[fieldKey]
  if (typeof val !== 'string') return []
  const vars = []
  let m
  while ((m = BRACKET_VAR_RE.exec(val)) !== null) {
    if (!vars.includes(m[1])) vars.push(m[1])
  }
  BRACKET_VAR_RE.lastIndex = 0
  return vars
}

function updateVar(varName, value) {
  if (!localParams.value._tvars) {
    localParams.value._tvars = {}
  }
  localParams.value._tvars[varName] = value
  emit('update:params', { ...localParams.value })
  emit('update:modelValue', { ...localParams.value })
}

// Backend returns pre-translated labels/descriptions — just render
function getFieldLabel(field) {
  return field.label
}

function getFieldDescription(field) {
  return field.description
}

/**
 * Evaluate a single condition against a current value.
 * Supports: array (includes), object operators ($in, $ne, $notEmpty), or single value.
 */
function evaluateCondition(currentValue, condition) {
  if (Array.isArray(condition)) {
    return condition.includes(currentValue)
  }
  if (condition && typeof condition === 'object') {
    if ('$in' in condition) {
      return Array.isArray(condition.$in) && condition.$in.includes(currentValue)
    }
    if ('$ne' in condition) {
      return currentValue !== condition.$ne
    }
    if ('$notEmpty' in condition) {
      const isEmpty = currentValue === undefined || currentValue === null || currentValue === ''
      return condition.$notEmpty ? !isEmpty : isEmpty
    }
    return false
  }
  return currentValue === condition
}

/**
 * Check if a field should be visible based on showIf/hideIf/displayOptions/showWhen
 */
function isFieldVisible(field, currentValues) {
  if (!field.displayOptions && !field.showWhen && !field.showIf && !field.hideIf) {
    return true
  }

  // showIf: ALL conditions must match for field to be visible
  // Note: currentValues already includes schema defaults via _mergeDefaults()
  if (field.showIf) {
    const showIfMet = Object.entries(field.showIf).every(([dependsOn, condition]) => {
      return evaluateCondition(currentValues[dependsOn], condition)
    })
    if (!showIfMet) return false
  }

  // hideIf: ANY condition matching hides the field
  if (field.hideIf) {
    const hideIfMet = Object.entries(field.hideIf).some(([dependsOn, condition]) => {
      return evaluateCondition(currentValues[dependsOn], condition)
    })
    if (hideIfMet) return false
  }

  // n8n-style displayOptions
  if (field.displayOptions) {
    const { show, hide } = field.displayOptions

    if (show) {
      const showConditionMet = Object.entries(show).every(([dependsOn, condition]) => {
        return evaluateCondition(currentValues[dependsOn], condition)
      })
      if (!showConditionMet) return false
    }

    if (hide) {
      const hideConditionMet = Object.entries(hide).some(([dependsOn, condition]) => {
        return evaluateCondition(currentValues[dependsOn], condition)
      })
      if (hideConditionMet) return false
    }
  }

  // Legacy showWhen
  if (field.showWhen) {
    const conditionMet = Object.entries(field.showWhen).every(([dependsOn, expected]) => {
      const currentValue = currentValues[dependsOn]
      if (Array.isArray(expected)) {
        return expected.includes(currentValue)
      }
      return currentValue === expected
    })
    if (!conditionMet) return false
  }

  return true
}

// ============================================
// Original mode (visibilityMode = null): basic/expert split
// ============================================

const basicFields = computed(() => {
  return fields.value.filter(f =>
    !f.expert &&
    !f.hidden &&
    isFieldVisible(f, localParams.value)
  )
})

const expertFields = computed(() => {
  return fields.value.filter(f =>
    f.expert &&
    !f.hidden &&
    isFieldVisible(f, localParams.value)
  )
})

// ============================================
// Visibility mode: field filtering + grouping
// ============================================

const hasExpertFields = computed(() => {
  return fields.value.some(f => f.expert && !f.hidden)
})

const visibleFieldsByMode = computed(() => {
  return fields.value.filter(f => {
    if (f.hidden) return false
    if (!isFieldVisible(f, localParams.value)) return false

    if (props.visibilityMode === 'simple') {
      if (f.expert) return showExpert.value
      return true
    }

    if (props.visibilityMode === 'advanced') {
      return true
    }

    // 'all' mode: everything except hidden
    return true
  })
})

const groupedFields = computed(() => {
  const groups = {}

  for (const field of visibleFieldsByMode.value) {
    const groupName = field.group || 'basic'
    if (!groups[groupName]) {
      groups[groupName] = []
    }
    groups[groupName].push(field)
  }

  return GROUP_ORDER
    .filter(g => groups[g] && groups[g].length > 0)
    .map(g => ({
      name: g,
      fields: groups[g],
      collapsed: collapsedGroups[g] ?? (g === 'advanced')
    }))
})

const hasMultipleGroups = computed(() => groupedFields.value.length > 1)

function toggleGroup(groupName) {
  collapsedGroups[groupName] = !(collapsedGroups[groupName] ?? (groupName === 'advanced'))
}

const showExpertToggleButton = computed(() => {
  return props.visibilityMode === 'simple' &&
         props.allowExpertToggle &&
         hasExpertFields.value &&
         !showExpert.value
})

// ============================================
// Generic Mode (no schema fallback)
// ============================================

const hasParams = computed(() => {
  return props.params && Object.keys(props.params).length > 0
})

const visibleParams = computed(() => {
  if (!props.params) return {}
  const schemaKeys = props.schema?.properties ? new Set(Object.keys(props.schema.properties)) : null
  return Object.fromEntries(
    Object.entries(props.params).filter(([key]) => {
      if (!key || !key.trim()) return false
      // If schema exists, only show params that match schema keys (flyto-core SSOT)
      if (schemaKeys && !schemaKeys.has(key)) return false
      return !props.schema?.properties?.[key]?.hidden
    })
  )
})

function inferInputType(value) {
  if (typeof value === 'boolean') return 'boolean'
  if (typeof value === 'number') return 'number'
  if (typeof value === 'string' && value.length > 100) return 'textarea'
  return 'text'
}

// Update a single parameter
function updateParam(key, value) {
  localParams.value[key] = value
  emit('update:params', { ...localParams.value })
  emit('update:modelValue', { ...localParams.value })
}

/**
 * Auto-switch the method param (type_method, click_method) when the user
 * selects an element that doesn't match the current valueKey.
 * e.g. type_method=placeholder but selected input only has name → switch to name.
 */
function onAutoSwitchMethod(field, payload) {
  const methodKey = field.ui?.value_key_from
  if (!methodKey) return

  // payload can be { method, value } (batched) or just a string (legacy)
  if (typeof payload === 'object' && payload.method) {
    // Atomic update: set method + value in one shot to prevent showIf flicker
    localParams.value[methodKey] = payload.method
    localParams.value[field.key] = payload.value
  } else {
    localParams.value[methodKey] = payload
  }
  emit('update:params', { ...localParams.value })
  emit('update:modelValue', { ...localParams.value })
}

</script>

<style scoped>
.schema-params-renderer {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* Loading & Empty States */
.loading-state,
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: #64748b;
  font-size: 12px;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Form Container */
.params-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 14px;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid #334155;
  border-radius: 8px;
}

/* Field Styling */
.param-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.param-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 500;
  color: #94a3b8;
}

.label-text {
  flex-shrink: 0;
}

.required-mark {
  color: #ef4444;
  font-weight: 600;
}

.label-hint {
  display: flex;
  align-items: center;
  color: #64748b;
  cursor: help;
  transition: color 0.15s;
}

.label-hint:hover {
  color: #8B5CF6;
}

/* Error Display */
.field-error {
  font-size: 12px;
  color: #ef4444;
  margin: 0;
}

/* Expert Section (original mode) */
.expert-section {
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid rgba(71, 85, 105, 0.3);
}

.expert-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 6px;
  color: #94a3b8;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.expert-toggle:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.3);
  color: #a78bfa;
}

.expert-toggle svg {
  transition: transform 0.2s;
}

.expert-toggle svg.rotated {
  transform: rotate(90deg);
}

.expert-count {
  margin-left: auto;
  padding: 2px 6px;
  background: rgba(139, 92, 246, 0.2);
  border-radius: 4px;
  font-size: 10px;
  color: #a78bfa;
}

.expert-fields {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 12px;
  padding: 12px;
  background: rgba(15, 23, 42, 0.3);
  border-radius: 6px;
}

/* Slide Transition */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Field Groups (visibilityMode) */
.field-group {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  background: rgba(51, 65, 85, 0.3);
  color: #94a3b8;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all 0.2s;
}

.group-header:hover {
  background: rgba(51, 65, 85, 0.5);
  color: #e2e8f0;
}

.group-chevron {
  transition: transform 0.2s;
}

.group-chevron.is-expanded {
  transform: rotate(90deg);
}

.group-title {
  flex: 1;
  text-align: left;
}

.group-count {
  color: #64748b;
  font-weight: 400;
}

.group-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* Show/Hide Advanced Toggle (visibilityMode) */
.show-advanced {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  border: 1px dashed #334155;
  border-radius: 8px;
  background: transparent;
  color: #64748b;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.show-advanced:hover {
  border-color: #475569;
  color: #94a3b8;
}

.rotate-180 {
  transform: rotate(180deg);
}

/* Dynamic [[var]] input fields */
.dynamic-var-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 4px;
  margin-left: 16px;
  padding-left: 10px;
  border-left: 2px solid rgba(139, 92, 246, 0.3);
}

.dynamic-var-label {
  color: #a78bfa;
  font-family: monospace;
  font-size: 11px;
}

/* Compact Mode */
.schema-params-renderer.compact {
  gap: 10px;
}

.schema-params-renderer.compact .params-form {
  gap: 10px;
  padding: 10px;
}

.schema-params-renderer.compact .param-field {
  gap: 4px;
}

.schema-params-renderer.compact .param-label {
  font-size: 10px;
}

.schema-params-renderer.compact .group-content {
  gap: 10px;
}

.schema-params-renderer.compact .field-group {
  gap: 10px;
}
</style>

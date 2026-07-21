/**
 * Value Source Composable
 * Handles value source logic for template parameters
 */

import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useModulesStore } from '@/stores/modulesStore'
import { resolveModuleLabel } from '@/utils/moduleIdUtils'
import {
  Pencil, FormInput, GitBranch, Code, Type, Hash,
  ToggleLeft, Calendar, Upload, List, Globe, Database, Settings, Palette
} from 'lucide-vue-next'

/**
 * Create value source composable
 * @param {Object} props - Component props (modelValue, inputType, uiInputFields, previousSteps)
 * @param {Function} emit - Emit function
 * @param {Ref} selectorRef - Ref to the selector element for click outside handling
 */
export function useValueSource(props, emit, selectorRef) {
  const { t } = useI18n()
  const modulesStore = useModulesStore()

  const isSourceOpen = ref(false)
  const isLinkedOpen = ref(false)

  /**
   * Extract the step ID from a ${...} expression if it references a known previous step.
   * Handles both ${steps.xxx.field} and ${xxx.field} formats.
   * Returns the step ID or null.
   */
  const _extractStepId = (val) => {
    if (!val.startsWith('${') || !val.endsWith('}')) return null
    const inner = val.slice(2, -1) // e.g. "steps.fetch_weather.data.result" or "build_report.data.result"
    const parts = inner.split('.')
    // ${steps.xxx...} → step ID is parts[1]
    if (parts[0] === 'steps' && parts.length >= 2) return parts[1]
    // ${xxx...} → step ID is parts[0], check against previousSteps
    if (parts[0] === 'loop') return null // loop is handled separately
    if (parts[0] === 'params' || parts[0] === 'env' || parts[0] === 'global') return null
    const stepIds = (props.previousSteps || []).map(s => s.id)
    if (stepIds.includes(parts[0])) return parts[0]
    return null
  }

  // Determine initial source type from value
  const getInitialSourceType = () => {
    const val = props.modelValue
    if (typeof val === 'string') {
      if (/^\{\{\w+\}\}$/.test(val)) return 'ui_input'
      if (/^\$\{params\.ui\.\w+\}$/.test(val)) return 'ui_input'
      if (val.startsWith('${loop.')) return 'previous_step'
      if (_extractStepId(val)) return 'previous_step'
      if (val.startsWith('${')) return 'expression'
    }
    return 'static'
  }

  const sourceType = ref(getInitialSourceType())
  const localValue = ref(props.modelValue)
  const selectedUIInput = ref('')
  const selectedStep = ref('')

  // Parse existing value
  const parseExistingValue = () => {
    const val = props.modelValue
    if (typeof val === 'string') {
      const bracketMatch = val.match(/^\{\{(\w+)\}\}$/)
      if (bracketMatch) {
        selectedUIInput.value = bracketMatch[1]
        sourceType.value = 'ui_input'
        return
      }
      // Normalize ${params.ui.xxx} → {{xxx}} (canonical UI input format)
      const paramsUiMatch = val.match(/^\$\{params\.ui\.(\w+)\}$/)
      if (paramsUiMatch) {
        const varName = paramsUiMatch[1]
        selectedUIInput.value = varName
        sourceType.value = 'ui_input'
        // Emit canonical format to gradually unify stored data
        emit('update:modelValue', `{{${varName}}}`)
        return
      }
      const loopMatch = val.match(/^\$\{(loop\.\w+)\}$/)
      if (loopMatch) {
        selectedStep.value = loopMatch[1]
        sourceType.value = 'previous_step'
        return
      }
      // Detect step references: ${steps.xxx.field} or ${xxx.field} where xxx is a known step
      const stepId = _extractStepId(val)
      if (stepId) {
        const inner = val.slice(2, -1) // e.g. "steps.fetch_weather.data.result"
        // Normalize to steps.xxx.yyy format for selectedStep
        selectedStep.value = inner.startsWith('steps.') ? inner : `steps.${inner}`
        sourceType.value = 'previous_step'
        return
      }
      if (val.startsWith('${') && val.endsWith('}')) {
        localValue.value = val.slice(2, -1)
        sourceType.value = 'expression'
        return
      }
    }
    localValue.value = val
    sourceType.value = 'static'
  }

  // Click outside handler
  function handleClickOutside(event) {
    if (selectorRef.value && !selectorRef.value.contains(event.target)) {
      isSourceOpen.value = false
      isLinkedOpen.value = false
    }
  }

  onMounted(() => {
    parseExistingValue()
    document.addEventListener('click', handleClickOutside)
  })

  onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside)
  })

  // Computed: linked display text
  const linkedDisplayText = computed(() => {
    if (sourceType.value === 'ui_input') {
      if (selectedUIInput.value) {
        const field = props.uiInputFields.find(f => f.variableName === selectedUIInput.value)
        return field ? (field.label || field.variableName) : selectedUIInput.value
      }
      return t('valueSource.selectUIField')
    } else if (sourceType.value === 'previous_step') {
      if (selectedStep.value) {
        // Loop context variable (e.g., 'loop.item')
        if (!selectedStep.value.startsWith('steps.')) {
          const step = props.previousSteps.find(s => s.id === selectedStep.value)
          return step?.label || selectedStep.value
        }
        // Extract step ID: "steps.build_report.data.result" → "build_report"
        const afterSteps = selectedStep.value.replace('steps.', '')
        const stepId = afterSteps.split('.')[0]
        const step = props.previousSteps.find(s => s.id === stepId)
        return step ? (resolveModuleLabel(step.module, modulesStore) || step.id) : stepId
      }
      return t('valueSource.selectStepOutput')
    }
    return ''
  })

  // Source options
  const sourceOptions = computed(() => [
    {
      value: 'static',
      label: t('valueSource.sources.static.label'),
      description: t('valueSource.sources.static.description'),
      icon: Pencil
    },
    {
      value: 'ui_input',
      label: t('valueSource.sources.uiInput.label'),
      description: t('valueSource.sources.uiInput.description'),
      icon: FormInput
    },
    {
      value: 'previous_step',
      label: t('valueSource.sources.previousStep.label'),
      description: t('valueSource.sources.previousStep.description'),
      icon: GitBranch
    },
    {
      value: 'expression',
      label: t('valueSource.sources.expression.label'),
      description: t('valueSource.sources.expression.description'),
      icon: Code
    }
  ])

  // Field type icons
  function getFieldIcon(type) {
    const icons = {
      'form.input_text': Type,
      'form.input_number': Hash,
      'form.input_select': List,
      'form.input_checkbox': ToggleLeft,
      'form.input_toggle': ToggleLeft,
      'form.input_date': Calendar,
      'form.input_file': Upload,
      'form.input_color': Palette
    }
    return icons[type] || Type
  }

  function getModuleIcon(module) {
    if (!module) return Settings
    const category = module.split('.')[0]
    const icons = {
      browser: Globe,
      scraper: Database,
      api: Globe,
      form: FormInput
    }
    return icons[category] || Settings
  }

  // Dropdown handlers
  function toggleSourceDropdown() {
    isSourceOpen.value = !isSourceOpen.value
    isLinkedOpen.value = false
  }

  function toggleLinkedDropdown() {
    isLinkedOpen.value = !isLinkedOpen.value
    isSourceOpen.value = false
  }

  function selectSource(value) {
    const oldType = sourceType.value
    sourceType.value = value
    isSourceOpen.value = false

    if (value === 'static') {
      if (oldType !== 'static') {
        localValue.value = ''
        emit('update:modelValue', '')
      }
    } else if (value === 'ui_input') {
      selectedUIInput.value = ''
      if (oldType !== 'ui_input') {
        isLinkedOpen.value = true
      }
    } else if (value === 'previous_step') {
      selectedStep.value = ''
      if (oldType !== 'previous_step') {
        isLinkedOpen.value = true
      }
    } else if (value === 'expression') {
      if (oldType !== 'expression') {
        localValue.value = ''
      }
    }
  }

  function selectUIInput(field) {
    selectedUIInput.value = field.variableName
    isLinkedOpen.value = false
    emit('update:modelValue', `{{${field.variableName}}}`)
  }

  function selectPreviousStep(step) {
    if (step.module === '__loop_context__') {
      selectedStep.value = step.id
      isLinkedOpen.value = false
      emit('update:modelValue', step.expression)
    } else {
      selectedStep.value = `steps.${step.id}.result`
      isLinkedOpen.value = false
      emit('update:modelValue', `\${steps.${step.id}.result}`)
    }
  }

  function emitValue() {
    if (sourceType.value === 'expression') {
      emit('update:modelValue', `\${${localValue.value}}`)
    } else {
      emit('update:modelValue', localValue.value)
    }
  }

  // Watch for external value changes
  watch(() => props.modelValue, (newVal) => {
    if (newVal !== localValue.value) {
      parseExistingValue()
    }
  })

  // Re-evaluate when previousSteps becomes available (step references may reclassify)
  watch(() => props.previousSteps?.length, () => {
    if (sourceType.value === 'expression' && _extractStepId(props.modelValue)) {
      parseExistingValue()
    }
  })

  return {
    // State
    sourceType,
    localValue,
    selectedUIInput,
    selectedStep,
    isSourceOpen,
    isLinkedOpen,
    // Computed
    linkedDisplayText,
    sourceOptions,
    // Methods
    getFieldIcon,
    getModuleIcon,
    toggleSourceDropdown,
    toggleLinkedDropdown,
    selectSource,
    selectUIInput,
    selectPreviousStep,
    emitValue
  }
}

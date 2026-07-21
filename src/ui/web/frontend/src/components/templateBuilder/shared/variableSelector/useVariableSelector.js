/**
 * Variable Selector Composable
 * Handles variable filtering, selection, and tab logic
 */
import { ref, computed, watch } from 'vue'
import { DATA_TYPES, VARIABLE_SOURCES } from '@/constants/templateBuilder/bindingTypes'
import {
  Type, Hash, ToggleLeft, Image, FileText, Layers, Package
} from 'lucide-vue-next'

const TYPE_ICONS = {
  [DATA_TYPES.STRING]: Type,
  [DATA_TYPES.NUMBER]: Hash,
  [DATA_TYPES.BOOLEAN]: ToggleLeft,
  [DATA_TYPES.IMAGE]: Image,
  [DATA_TYPES.FILE]: FileText,
  [DATA_TYPES.ARRAY]: Layers,
  [DATA_TYPES.OBJECT]: Package
}

export function useVariableSelector(props, emit) {
  const activeTab = ref('inputs')
  const searchQuery = ref('')
  const selectedVariable = ref(null)

  const currentTabVariables = computed(() => {
    return props.availableVariables[activeTab.value] || []
  })

  const filteredVariables = computed(() => {
    let vars = currentTabVariables.value

    if (props.filterTypes) {
      const allowedTypes = Array.isArray(props.filterTypes)
        ? props.filterTypes
        : [props.filterTypes]

      if (!allowedTypes.includes(DATA_TYPES.ANY)) {
        vars = vars.filter(v =>
          v.dataType === DATA_TYPES.ANY || allowedTypes.includes(v.dataType)
        )
      }
    }

    if (searchQuery.value.trim()) {
      const query = searchQuery.value.toLowerCase()
      vars = vars.filter(v =>
        v.label.toLowerCase().includes(query) ||
        v.path.toLowerCase().includes(query) ||
        v.expression.toLowerCase().includes(query)
      )
    }

    return vars
  })

  function getVariableIcon(variable) {
    return TYPE_ICONS[variable.dataType] || Type
  }

  function isSelected(variable) {
    return selectedVariable.value?.path === variable.path
  }

  function selectVariable(variable) {
    selectedVariable.value = variable
    if (props.mode === 'inline') {
      emit('select', variable)
      emit('update:modelValue', variable.expression)
    }
  }

  function confirmSelection() {
    if (selectedVariable.value) {
      emit('select', selectedVariable.value)
      emit('update:modelValue', selectedVariable.value.expression)
    }
  }

  function clearSearch() {
    searchQuery.value = ''
  }

  function setActiveTab(tabId) {
    activeTab.value = tabId
  }

  watch(() => props.modelValue, (newValue, oldValue) => {
    if (newValue !== oldValue) {
      searchQuery.value = ''
    }
    if (newValue) {
      for (const tabId of ['inputs', 'steps', 'env']) {
        const vars = props.availableVariables[tabId] || []
        const found = vars.find(v => v.expression === newValue)
        if (found) {
          selectedVariable.value = found
          activeTab.value = tabId
          break
        }
      }
    }
  }, { immediate: true })

  return {
    activeTab,
    searchQuery,
    selectedVariable,
    filteredVariables,
    getVariableIcon,
    isSelected,
    selectVariable,
    confirmSelection,
    clearSearch,
    setActiveTab
  }
}

export { TYPE_ICONS, DATA_TYPES, VARIABLE_SOURCES }

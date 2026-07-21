import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'

const mockT = vi.fn((key) => key)
vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: mockT })
}))

vi.mock('@/stores/modulesStore', () => ({
  useModulesStore: () => ({ modulesMetadata: {} })
}))

vi.mock('@/utils/moduleIdUtils', () => ({
  resolveModuleLabel: vi.fn((mod) => mod)
}))

// Mock lifecycle hooks
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return {
    ...actual,
    onMounted: vi.fn((cb) => cb()),
    onUnmounted: vi.fn()
  }
})

vi.mock('lucide-vue-next', () => ({
  Pencil: 'Pencil',
  FormInput: 'FormInput',
  GitBranch: 'GitBranch',
  Code: 'Code',
  Type: 'Type',
  Hash: 'Hash',
  ToggleLeft: 'ToggleLeft',
  Calendar: 'Calendar',
  Upload: 'Upload',
  List: 'List',
  Globe: 'Globe',
  Database: 'Database',
  Settings: 'Settings',
  Palette: 'Palette'
}))

import { useValueSource } from '@/composables/useValueSource'

describe('useValueSource', () => {
  let emit, selectorRef

  function createComposable(modelValue, options = {}) {
    const props = {
      modelValue,
      inputType: options.inputType || 'text',
      uiInputFields: options.uiInputFields || [],
      previousSteps: options.previousSteps || []
    }
    emit = vi.fn()
    selectorRef = ref(null)
    return useValueSource(props, emit, selectorRef)
  }

  describe('initial source type detection', () => {
    it('detects static values', () => {
      const { sourceType } = createComposable('hello')
      expect(sourceType.value).toBe('static')
    })

    it('detects UI input {{var}} format', () => {
      const { sourceType, selectedUIInput } = createComposable('{{username}}')
      expect(sourceType.value).toBe('ui_input')
      expect(selectedUIInput.value).toBe('username')
    })

    it('detects UI input ${params.ui.var} format and normalizes', () => {
      const { sourceType } = createComposable('${params.ui.email}')
      expect(sourceType.value).toBe('ui_input')
      // Should emit canonical format
      expect(emit).toHaveBeenCalledWith('update:modelValue', '{{email}}')
    })

    it('detects step references ${steps.xxx.field}', () => {
      const { sourceType, selectedStep } = createComposable('${steps.fetch_data.result}', {
        previousSteps: [{ id: 'fetch_data', module: 'api.get' }]
      })
      expect(sourceType.value).toBe('previous_step')
      expect(selectedStep.value).toBe('steps.fetch_data.result')
    })

    it('detects loop references', () => {
      const { sourceType } = createComposable('${loop.item}')
      expect(sourceType.value).toBe('previous_step')
    })

    it('detects expression values', () => {
      const { sourceType, localValue } = createComposable('${env.API_KEY}')
      expect(sourceType.value).toBe('expression')
      expect(localValue.value).toBe('env.API_KEY')
    })

    it('treats non-string values as static', () => {
      const { sourceType } = createComposable(42)
      expect(sourceType.value).toBe('static')
    })
  })

  describe('sourceOptions', () => {
    it('provides 4 source options', () => {
      const { sourceOptions } = createComposable('')
      expect(sourceOptions.value).toHaveLength(4)
      const values = sourceOptions.value.map(o => o.value)
      expect(values).toEqual(['static', 'ui_input', 'previous_step', 'expression'])
    })
  })

  describe('getFieldIcon', () => {
    it('returns matching icon for known types', () => {
      const { getFieldIcon } = createComposable('')
      expect(getFieldIcon('form.input_text')).toBe('Type')
      expect(getFieldIcon('form.input_number')).toBe('Hash')
      expect(getFieldIcon('form.input_select')).toBe('List')
    })

    it('returns default Type for unknown types', () => {
      const { getFieldIcon } = createComposable('')
      expect(getFieldIcon('unknown.type')).toBe('Type')
    })
  })

  describe('getModuleIcon', () => {
    it('returns matching icon for known categories', () => {
      const { getModuleIcon } = createComposable('')
      expect(getModuleIcon('browser.click')).toBe('Globe')
      expect(getModuleIcon('api.get')).toBe('Globe')
      expect(getModuleIcon('form.input')).toBe('FormInput')
    })

    it('returns Settings for unknown/null module', () => {
      const { getModuleIcon } = createComposable('')
      expect(getModuleIcon(null)).toBe('Settings')
      expect(getModuleIcon('unknown.module')).toBe('Settings')
    })
  })

  describe('selectSource', () => {
    it('changes source type to static and emits empty value', () => {
      const vs = createComposable('{{test}}')
      vs.selectSource('static')
      expect(vs.sourceType.value).toBe('static')
      expect(emit).toHaveBeenCalledWith('update:modelValue', '')
    })

    it('changes source type to ui_input and opens linked dropdown', () => {
      const vs = createComposable('hello')
      vs.selectSource('ui_input')
      expect(vs.sourceType.value).toBe('ui_input')
      expect(vs.isLinkedOpen.value).toBe(true)
    })

    it('changes source type to previous_step and opens linked dropdown', () => {
      const vs = createComposable('hello')
      vs.selectSource('previous_step')
      expect(vs.sourceType.value).toBe('previous_step')
      expect(vs.isLinkedOpen.value).toBe(true)
    })
  })

  describe('selectUIInput', () => {
    it('selects UI field and emits {{var}} format', () => {
      const vs = createComposable('')
      vs.selectUIInput({ variableName: 'email', label: 'Email' })
      expect(vs.selectedUIInput.value).toBe('email')
      expect(emit).toHaveBeenCalledWith('update:modelValue', '{{email}}')
      expect(vs.isLinkedOpen.value).toBe(false)
    })
  })

  describe('selectPreviousStep', () => {
    it('selects a regular step and emits ${steps.xxx.result}', () => {
      const vs = createComposable('')
      vs.selectPreviousStep({ id: 'fetch_data', module: 'api.get' })
      expect(vs.selectedStep.value).toBe('steps.fetch_data.result')
      expect(emit).toHaveBeenCalledWith('update:modelValue', '${steps.fetch_data.result}')
    })

    it('handles loop context steps', () => {
      const vs = createComposable('')
      vs.selectPreviousStep({ id: 'loop.item', module: '__loop_context__', expression: '${loop.item}' })
      expect(vs.selectedStep.value).toBe('loop.item')
      expect(emit).toHaveBeenCalledWith('update:modelValue', '${loop.item}')
    })
  })

  describe('emitValue', () => {
    it('wraps expression values in ${}', () => {
      const vs = createComposable('')
      vs.sourceType.value = 'expression'
      vs.localValue.value = 'env.SECRET'
      vs.emitValue()
      expect(emit).toHaveBeenCalledWith('update:modelValue', '${env.SECRET}')
    })

    it('emits static values directly', () => {
      const vs = createComposable('')
      vs.sourceType.value = 'static'
      vs.localValue.value = 'plain text'
      vs.emitValue()
      expect(emit).toHaveBeenCalledWith('update:modelValue', 'plain text')
    })
  })

  describe('toggleSourceDropdown', () => {
    it('toggles source dropdown and closes linked', () => {
      const vs = createComposable('')
      vs.isLinkedOpen.value = true
      vs.toggleSourceDropdown()
      expect(vs.isSourceOpen.value).toBe(true)
      expect(vs.isLinkedOpen.value).toBe(false)
    })
  })

  describe('toggleLinkedDropdown', () => {
    it('toggles linked dropdown and closes source', () => {
      const vs = createComposable('')
      vs.isSourceOpen.value = true
      vs.toggleLinkedDropdown()
      expect(vs.isLinkedOpen.value).toBe(true)
      expect(vs.isSourceOpen.value).toBe(false)
    })
  })
})

import { describe, it, expect } from 'vitest'
import { createMetadataState } from '@/stores/builder/metadata/state'
import { createTemplateActions } from '@/stores/builder/metadata/templateActions'

describe('builder metadata data boundary', () => {
  it('loads partial template payloads into stable defaults', () => {
    const state = createMetadataState()
    const actions = createTemplateActions(state)

    actions.loadTemplate({
      id: 'tpl-1',
      name: 'Imported',
      ui: { sections: 'bad' }
    })

    expect(state.existingTemplateId.value).toBe('tpl-1')
    expect(state.templateName.value).toBe('Imported')
    expect(state.sections.value).toEqual([])
    expect(state.loadError.value).toBeNull()
  })

  it('does not throw when template payload is missing', () => {
    const state = createMetadataState()
    const actions = createTemplateActions(state)

    actions.loadTemplate(null)

    expect(state.existingTemplateId.value).toBeNull()
    expect(state.templateId.value).toBe('new_template')
    expect(state.templateName.value).toBe('')
    expect(state.sections.value).toEqual([])
    expect(state.loadError.value).toBe('Invalid template payload')
    expect(state.isLoading.value).toBe(false)
  })
})

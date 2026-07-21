import { describe, it, expect, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import TriggerConfigPanel from '@/components/triggers/TriggerConfigPanel.vue'

vi.mock('@/api/triggers', () => ({
  validateCron: vi.fn(),
}))

function factory(props = {}) {
  return shallowMount(TriggerConfigPanel, {
    props: {
      params: {},
      ...props,
    },
    global: {
      mocks: {
        $t: (_key, fallback) => (typeof fallback === 'string' ? fallback : _key),
      },
    },
  })
}

describe('TriggerConfigPanel', () => {
  it('exposes MCP as a selectable trigger type', async () => {
    const wrapper = factory()

    const mcpButton = wrapper.findAll('button').find((button) => button.text() === 'MCP')
    expect(mcpButton).toBeTruthy()

    await mcpButton.trigger('click')

    expect(wrapper.emitted('update:params')[0][0]).toEqual({ trigger_type: 'mcp' })
  })

  it('renders MCP tool metadata fields and emits updates', async () => {
    const wrapper = factory({
      params: {
        trigger_type: 'mcp',
        tool_name: 'run_project_smoke',
        tool_description: 'Run project smoke',
      },
    })

    expect(wrapper.text()).toContain('Tool Name')
    expect(wrapper.text()).toContain('Description')

    const inputs = wrapper.findAll('input')
    expect(inputs[0].element.value).toBe('run_project_smoke')
    expect(inputs[1].element.value).toBe('Run project smoke')

    await inputs[0].setValue('run_security_smoke')

    expect(wrapper.emitted('update:params')[0][0]).toEqual({
      trigger_type: 'mcp',
      tool_name: 'run_security_smoke',
      tool_description: 'Run project smoke',
    })
  })
})

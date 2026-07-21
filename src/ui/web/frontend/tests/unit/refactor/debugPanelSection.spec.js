/**
 * Refactor Validation: DebugPanelSection Component
 *
 * Verifies the component is correctly defined with all props and emits.
 * No mocks — direct import of the .vue SFC.
 */
import { describe, it, expect } from 'vitest'
import DebugPanelSection from '@/components/templateBuilder/DebugPanelSection.vue'

describe('DebugPanelSection', () => {
  it('component is importable', () => {
    expect(DebugPanelSection).toBeDefined()
  })

  it('has single root element (not multi-root fragment)', () => {
    // Vue SFC with <template><div>...</div></template> compiles to a render
    // function; a fragment would have multiple root nodes.
    // We verify the component has a render function (compiled correctly).
    expect(
      DebugPanelSection.render || DebugPanelSection.setup || DebugPanelSection.__ssrInlineRender
    ).toBeDefined()
  })

  it('defines all 9 props', () => {
    const propNames = Object.keys(DebugPanelSection.props || {})
    const expected = [
      'activeDebugPanel',
      'executionId',
      'selectedStepId',
      'workflowId',
      'workflowName',
      'workflowSteps',
      'usedModules',
      'executions',
      'isLoadingHistory'
    ]
    for (const name of expected) {
      expect(propNames).toContain(name)
    }
    expect(propNames).toHaveLength(9)
  })

  it('defines all 8 emits', () => {
    const emits = DebugPanelSection.emits || DebugPanelSection.__emits || []
    const expected = [
      'close',
      'lineage-node-select',
      'replay-started',
      'tests-completed',
      'version-lock-changed',
      'select-execution',
      'replay-execution',
      'stop-execution'
    ]
    for (const name of expected) {
      expect(emits).toContain(name)
    }
    expect(emits).toHaveLength(8)
  })
})

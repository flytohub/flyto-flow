/**
 * nodeService Unit Tests
 */
import { describe, it, expect, vi } from 'vitest'

// Mock the component registry
vi.mock('@/config/nodeComponentRegistry', () => ({
  getNodeComponent: vi.fn((type) => `Component_${type}`)
}))

import {
  nodeService,
  getType,
  getUiConfig,
  getInputHandles,
  getOutputHandles,
  getDynamicHandlesConfig,
  resolve,
  getComponent,
  getDefaultParams,
  isBranch,
  isSwitch,
  isLoop,
  isContainer,
  isMerge,
  isFork,
  isJoin,
  isSubflow,
  isTrigger,
  isStart,
  isEnd,
  isErrorTrigger,
  isCode,
  isHttp,
  isLLMChain,
  isVectorStore,
  isAIAgent,
  isFlowControl,
  isEntryPoint,
  isTerminal,
  isMultiOutput,
  shouldShowAddButton,
  // Backward compat aliases
  getNodeType,
  resolveNode,
  getNodeComponent,
  isBranchNode,
  isLoopNode
} from '@/services/nodeService'

// Helper: create mock modules store
function createStore(metadata = {}) {
  return { modulesMetadata: metadata }
}

describe('nodeService', () => {
  // =========================================================================
  // getType
  // =========================================================================

  describe('getType', () => {
    it('should return "standard" for null moduleId', () => {
      expect(getType(null)).toBe('standard')
    })

    it('should return "standard" for empty moduleId', () => {
      expect(getType('')).toBe('standard')
    })

    it('should return "standard" when no store provided', () => {
      expect(getType('some.module')).toBe('standard')
    })

    it('should return "standard" when module not in store', () => {
      const store = createStore({})
      expect(getType('unknown.module', store)).toBe('standard')
    })

    it('should return nodeType from metadata', () => {
      const store = createStore({
        'flow.branch': { nodeType: 'branch' }
      })
      expect(getType('flow.branch', store)).toBe('branch')
    })

    it('should default to "standard" when metadata has no nodeType', () => {
      const store = createStore({
        'some.module': {}
      })
      expect(getType('some.module', store)).toBe('standard')
    })
  })

  // =========================================================================
  // getUiConfig
  // =========================================================================

  describe('getUiConfig', () => {
    it('should return empty object for no moduleId', () => {
      expect(getUiConfig(null)).toEqual({})
    })

    it('should return uiConfig from metadata', () => {
      const store = createStore({
        'mod.a': { uiConfig: { isFlowControl: true, styleClass: 'branch-node' } }
      })
      expect(getUiConfig('mod.a', store)).toEqual({ isFlowControl: true, styleClass: 'branch-node' })
    })

    it('should return empty object when metadata has no uiConfig', () => {
      const store = createStore({ 'mod.a': {} })
      expect(getUiConfig('mod.a', store)).toEqual({})
    })
  })

  // =========================================================================
  // getInputHandles / getOutputHandles
  // =========================================================================

  describe('getInputHandles', () => {
    it('should return empty array for null moduleId', () => {
      expect(getInputHandles(null)).toEqual([])
    })

    it('should return inputHandles from metadata', () => {
      const store = createStore({
        'mod.a': { inputHandles: [{ id: 'in1', position: 'left' }] }
      })
      expect(getInputHandles('mod.a', store)).toEqual([{ id: 'in1', position: 'left' }])
    })
  })

  describe('getOutputHandles', () => {
    it('should return empty array for null moduleId', () => {
      expect(getOutputHandles(null)).toEqual([])
    })

    it('should return outputHandles from metadata', () => {
      const store = createStore({
        'mod.a': { outputHandles: [{ id: 'out1' }] }
      })
      expect(getOutputHandles('mod.a', store)).toEqual([{ id: 'out1' }])
    })
  })

  // =========================================================================
  // getDynamicHandlesConfig
  // =========================================================================

  describe('getDynamicHandlesConfig', () => {
    it('should return null for null moduleId', () => {
      expect(getDynamicHandlesConfig(null)).toBeNull()
    })

    it('should return dynamicHandles from metadata', () => {
      const config = { fromParam: 'cases', idPrefix: 'case_', colors: ['#f00'] }
      const store = createStore({ 'mod.switch': { dynamicHandles: config } })
      expect(getDynamicHandlesConfig('mod.switch', store)).toEqual(config)
    })

    it('should return null when no dynamicHandles in metadata', () => {
      const store = createStore({ 'mod.a': {} })
      expect(getDynamicHandlesConfig('mod.a', store)).toBeNull()
    })
  })

  // =========================================================================
  // computeDynamicOutputs (tested via resolve)
  // =========================================================================

  describe('resolve - dynamic outputs', () => {
    it('should compute dynamic outputs from array param', () => {
      const store = createStore({
        'flow.switch': {
          nodeType: 'switch',
          uiConfig: {},
          inputHandles: [],
          outputHandles: [],
          dynamicHandles: {
            fromParam: 'cases',
            idPrefix: 'case_',
            position: 'right',
            colors: ['#f00', '#0f0', '#00f']
          }
        }
      })

      const params = {
        cases: [
          { id: 'a', value: 'alpha', label: 'Alpha' },
          { id: 'b', value: 'beta' }
        ]
      }

      const result = resolve('flow.switch', params, store)
      expect(result.handles.dynamicOutputs).toHaveLength(2)
      expect(result.handles.dynamicOutputs[0]).toEqual({
        id: 'a',
        position: 'right',
        color: '#f00',
        label: 'Alpha'
      })
      expect(result.handles.dynamicOutputs[1].label).toBe('beta')
    })

    it('should compute dynamic outputs from number param', () => {
      const store = createStore({
        'flow.fork': {
          nodeType: 'fork',
          uiConfig: {},
          inputHandles: [],
          outputHandles: [],
          dynamicHandles: {
            fromParam: 'branchCount',
            idPrefix: 'branch_',
            position: 'right',
            colors: ['#f00', '#0f0']
          }
        }
      })

      const result = resolve('flow.fork', { branchCount: 3 }, store)
      expect(result.handles.dynamicOutputs).toHaveLength(3)
      expect(result.handles.dynamicOutputs[0].id).toBe('branch_1')
      expect(result.handles.dynamicOutputs[2].id).toBe('branch_3')
      // Colors should cycle
      expect(result.handles.dynamicOutputs[2].color).toBe('#f00')
    })

    it('should return empty for missing param', () => {
      const store = createStore({
        'flow.fork': {
          nodeType: 'fork',
          dynamicHandles: { fromParam: 'branchCount', idPrefix: 'b_', colors: ['#f00'] }
        }
      })

      const result = resolve('flow.fork', {}, store)
      expect(result.handles.dynamicOutputs).toEqual([])
    })
  })

  // =========================================================================
  // resolve
  // =========================================================================

  describe('resolve', () => {
    it('should return fallback config when metadata not found', () => {
      const result = resolve('unknown.module', {}, createStore({}))
      expect(result).toEqual({
        type: 'standard',
        styleClass: '',
        isFlowControl: false,
        showAddButton: true,
        handles: { inputs: [], outputs: [] }
      })
    })

    it('should return full config from metadata', () => {
      const store = createStore({
        'flow.branch': {
          nodeType: 'branch',
          uiConfig: {
            styleClass: 'branch-style',
            isFlowControl: true,
            isLoop: false,
            showAddButton: false,
            showErrorHandle: true
          },
          inputHandles: [{ id: 'in' }],
          outputHandles: [{ id: 'true' }, { id: 'false' }]
        }
      })

      const result = resolve('flow.branch', {}, store)
      expect(result.type).toBe('branch')
      expect(result.styleClass).toBe('branch-style')
      expect(result.isFlowControl).toBe(true)
      expect(result.showAddButton).toBe(false)
      expect(result.showErrorHandle).toBe(true)
      expect(result.handles.inputs).toHaveLength(1)
      expect(result.handles.outputs).toHaveLength(2)
    })
  })

  // =========================================================================
  // getComponent
  // =========================================================================

  describe('getComponent', () => {
    it('should return component for standard node', () => {
      const store = createStore({ 'mod.a': { nodeType: 'standard' } })
      const comp = getComponent('mod.a', store)
      expect(comp).toBe('Component_standard')
    })

    it('should return ai_sub component for sub-node', () => {
      const comp = getComponent('mod.a', null, { isSubNode: true })
      expect(comp).toBe('Component_ai_sub')
    })

    it('should return ai_sub component for subNodeType', () => {
      const comp = getComponent('mod.a', null, { subNodeType: 'planner' })
      expect(comp).toBe('Component_ai_sub')
    })
  })

  // =========================================================================
  // getDefaultParams
  // =========================================================================

  describe('getDefaultParams', () => {
    it('should return default params from metadata', () => {
      const store = createStore({
        'mod.a': { defaultParams: { timeout: 30 } }
      })
      expect(getDefaultParams('mod.a', store)).toEqual({ timeout: 30 })
    })

    it('should return empty object when no defaults', () => {
      const store = createStore({ 'mod.a': {} })
      expect(getDefaultParams('mod.a', store)).toEqual({})
    })
  })

  // =========================================================================
  // Type check functions
  // =========================================================================

  describe('type check functions', () => {
    const typeChecks = [
      ['isBranch', isBranch, 'branch'],
      ['isSwitch', isSwitch, 'switch'],
      ['isLoop', isLoop, 'loop'],
      ['isContainer', isContainer, 'container'],
      ['isMerge', isMerge, 'merge'],
      ['isFork', isFork, 'fork'],
      ['isJoin', isJoin, 'join'],
      ['isSubflow', isSubflow, 'subflow'],
      ['isTrigger', isTrigger, 'trigger'],
      ['isStart', isStart, 'start'],
      ['isEnd', isEnd, 'end'],
      ['isErrorTrigger', isErrorTrigger, 'error_trigger'],
      ['isCode', isCode, 'code'],
      ['isHttp', isHttp, 'http'],
      ['isLLMChain', isLLMChain, 'llm_chain'],
      ['isVectorStore', isVectorStore, 'vector_store'],
      ['isAIAgent', isAIAgent, 'ai_agent']
    ]

    typeChecks.forEach(([fnName, fn, expectedType]) => {
      it(`${fnName} should return true for ${expectedType} type`, () => {
        const store = createStore({ 'mod.x': { nodeType: expectedType } })
        expect(fn('mod.x', store)).toBe(true)
      })

      it(`${fnName} should return false for different type`, () => {
        const store = createStore({ 'mod.x': { nodeType: 'standard' } })
        expect(fn('mod.x', store)).toBe(false)
      })
    })
  })

  // =========================================================================
  // isFlowControl
  // =========================================================================

  describe('isFlowControl', () => {
    it('should use uiConfig.isFlowControl when defined', () => {
      const store = createStore({
        'mod.a': { nodeType: 'standard', uiConfig: { isFlowControl: true } }
      })
      expect(isFlowControl('mod.a', store)).toBe(true)
    })

    it('should fallback to FLOW_CONTROL_TYPES set', () => {
      const store = createStore({ 'mod.a': { nodeType: 'branch', uiConfig: {} } })
      expect(isFlowControl('mod.a', store)).toBe(true)
    })

    it('should return false for standard nodes', () => {
      const store = createStore({ 'mod.a': { nodeType: 'standard', uiConfig: {} } })
      expect(isFlowControl('mod.a', store)).toBe(false)
    })
  })

  // =========================================================================
  // isEntryPoint
  // =========================================================================

  describe('isEntryPoint', () => {
    it('should use uiConfig.isEntryPoint when defined', () => {
      const store = createStore({
        'mod.a': { nodeType: 'standard', uiConfig: { isEntryPoint: true } }
      })
      expect(isEntryPoint('mod.a', store)).toBe(true)
    })

    it('should detect trigger as entry point', () => {
      const store = createStore({ 'mod.a': { nodeType: 'trigger', uiConfig: {} } })
      expect(isEntryPoint('mod.a', store)).toBe(true)
    })

    it('should detect start as entry point', () => {
      const store = createStore({ 'mod.a': { nodeType: 'start', uiConfig: {} } })
      expect(isEntryPoint('mod.a', store)).toBe(true)
    })

    it('should detect error_trigger as entry point', () => {
      const store = createStore({ 'mod.a': { nodeType: 'error_trigger', uiConfig: {} } })
      expect(isEntryPoint('mod.a', store)).toBe(true)
    })
  })

  // =========================================================================
  // isTerminal
  // =========================================================================

  describe('isTerminal', () => {
    it('should use uiConfig.isTerminal when defined', () => {
      const store = createStore({
        'mod.a': { nodeType: 'standard', uiConfig: { isTerminal: true } }
      })
      expect(isTerminal('mod.a', store)).toBe(true)
    })

    it('should detect end as terminal', () => {
      const store = createStore({ 'mod.a': { nodeType: 'end', uiConfig: {} } })
      expect(isTerminal('mod.a', store)).toBe(true)
    })

    it('should return false for non-terminal nodes', () => {
      const store = createStore({ 'mod.a': { nodeType: 'standard', uiConfig: {} } })
      expect(isTerminal('mod.a', store)).toBe(false)
    })
  })

  // =========================================================================
  // isMultiOutput
  // =========================================================================

  describe('isMultiOutput', () => {
    it('should use uiConfig.isMultiOutput when defined', () => {
      const store = createStore({
        'mod.a': { nodeType: 'standard', uiConfig: { isMultiOutput: true } }
      })
      expect(isMultiOutput('mod.a', store)).toBe(true)
    })

    it('should detect branch as multi-output', () => {
      const store = createStore({ 'mod.a': { nodeType: 'branch', uiConfig: {} } })
      expect(isMultiOutput('mod.a', store)).toBe(true)
    })

    it('should return false for standard node', () => {
      const store = createStore({ 'mod.a': { nodeType: 'standard', uiConfig: {} } })
      expect(isMultiOutput('mod.a', store)).toBe(false)
    })
  })

  // =========================================================================
  // shouldShowAddButton
  // =========================================================================

  describe('shouldShowAddButton', () => {
    it('should use uiConfig.showAddButton when defined', () => {
      const store = createStore({
        'mod.a': { nodeType: 'standard', uiConfig: { showAddButton: false } }
      })
      expect(shouldShowAddButton('mod.a', store)).toBe(false)
    })

    it('should return true for non-terminal nodes', () => {
      const store = createStore({ 'mod.a': { nodeType: 'standard', uiConfig: {} } })
      expect(shouldShowAddButton('mod.a', store)).toBe(true)
    })

    it('should return false for end nodes (terminal)', () => {
      const store = createStore({ 'mod.a': { nodeType: 'end', uiConfig: {} } })
      expect(shouldShowAddButton('mod.a', store)).toBe(false)
    })
  })

  // =========================================================================
  // Backward compatibility aliases
  // =========================================================================

  describe('backward compatibility aliases', () => {
    it('getNodeType should be same as getType', () => {
      expect(getNodeType).toBe(getType)
    })

    it('resolveNode should be same as resolve', () => {
      expect(resolveNode).toBe(resolve)
    })

    it('getNodeComponent should be same as getComponent', () => {
      expect(getNodeComponent).toBe(getComponent)
    })

    it('isBranchNode should be same as isBranch', () => {
      expect(isBranchNode).toBe(isBranch)
    })

    it('isLoopNode should be same as isLoop', () => {
      expect(isLoopNode).toBe(isLoop)
    })
  })

  // =========================================================================
  // nodeService object
  // =========================================================================

  describe('nodeService object', () => {
    it('should expose all core functions', () => {
      expect(nodeService.getType).toBe(getType)
      expect(nodeService.resolve).toBe(resolve)
      expect(nodeService.getComponent).toBe(getComponent)
      expect(nodeService.getDefaultParams).toBe(getDefaultParams)
    })

    it('should expose all type check functions', () => {
      expect(nodeService.isBranch).toBe(isBranch)
      expect(nodeService.isSwitch).toBe(isSwitch)
      expect(nodeService.isFlowControl).toBe(isFlowControl)
      expect(nodeService.isEntryPoint).toBe(isEntryPoint)
      expect(nodeService.isTerminal).toBe(isTerminal)
      expect(nodeService.isMultiOutput).toBe(isMultiOutput)
      expect(nodeService.shouldShowAddButton).toBe(shouldShowAddButton)
    })
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/api/client', () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  del: vi.fn()
}))

vi.mock('@/api/config', () => ({
  API_ENDPOINTS: {
    WORKFLOWS: {
      LIST: '/workflows',
      GET: (id) => `/workflows/${id}`,
      CREATE: '/workflows',
      UPDATE: (id) => `/workflows/${id}`,
      DELETE: (id) => `/workflows/${id}`,
      EXECUTE: (id) => `/workflows/${id}/execute`,
      RUN: '/workflows/run'
    }
  }
}))

import { get, post, put, del } from '@/api/client'
import { workflowAPI } from '@/api/workflows'

describe('Workflows API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // =========================================================================
  // list
  // =========================================================================

  describe('list()', () => {
    it('calls GET /workflows with no params by default', async () => {
      get.mockResolvedValue({ ok: true, workflows: [] })

      await workflowAPI.list()

      expect(get).toHaveBeenCalledWith('/workflows')
    })

    it('appends enabled filter param', async () => {
      get.mockResolvedValue({ ok: true, workflows: [] })

      await workflowAPI.list({ enabled: true })

      expect(get).toHaveBeenCalledWith('/workflows?enabled=true')
    })

    it('appends tags as comma-separated string', async () => {
      get.mockResolvedValue({ ok: true, workflows: [] })

      await workflowAPI.list({ tags: ['automation', 'browser'] })

      expect(get).toHaveBeenCalledWith('/workflows?tags=automation%2Cbrowser')
    })

    it('appends both enabled and tags', async () => {
      get.mockResolvedValue({ ok: true, workflows: [] })

      await workflowAPI.list({ enabled: false, tags: 'production' })

      const callUrl = get.mock.calls[0][0]
      expect(callUrl).toContain('enabled=false')
      expect(callUrl).toContain('tags=production')
    })
  })

  // =========================================================================
  // get
  // =========================================================================

  describe('get()', () => {
    it('calls GET /workflows/:id', async () => {
      get.mockResolvedValue({ ok: true, id: 'wf1', name: 'My Workflow' })

      const result = await workflowAPI.get('wf1')

      expect(get).toHaveBeenCalledWith('/workflows/wf1')
      expect(result.name).toBe('My Workflow')
    })
  })

  // =========================================================================
  // create
  // =========================================================================

  describe('create()', () => {
    it('calls POST /workflows with workflow data', async () => {
      const workflow = { name: 'New Workflow', steps: [] }
      post.mockResolvedValue({ ok: true, id: 'wf-new' })

      const result = await workflowAPI.create(workflow)

      expect(post).toHaveBeenCalledWith('/workflows', workflow)
      expect(result.id).toBe('wf-new')
    })
  })

  // =========================================================================
  // update
  // =========================================================================

  describe('update()', () => {
    it('calls PUT /workflows/:id with update data', async () => {
      put.mockResolvedValue({ ok: true })

      await workflowAPI.update('wf1', { name: 'Updated' })

      expect(put).toHaveBeenCalledWith('/workflows/wf1', { name: 'Updated' })
    })
  })

  // =========================================================================
  // delete
  // =========================================================================

  describe('delete()', () => {
    it('calls DELETE /workflows/:id', async () => {
      del.mockResolvedValue({ ok: true })

      await workflowAPI.delete('wf1')

      expect(del).toHaveBeenCalledWith('/workflows/wf1')
    })
  })

  // =========================================================================
  // execute
  // =========================================================================

  describe('execute()', () => {
    it('calls POST /workflows/:id/execute with params', async () => {
      post.mockResolvedValue({ ok: true, executionId: 'exec-1' })

      const result = await workflowAPI.execute('wf1', { url: 'https://example.com' })

      expect(post).toHaveBeenCalledWith('/workflows/wf1/execute', { url: 'https://example.com' })
      expect(result.executionId).toBe('exec-1')
    })

    it('passes empty params object by default', async () => {
      post.mockResolvedValue({ ok: true })

      await workflowAPI.execute('wf1')

      expect(post).toHaveBeenCalledWith('/workflows/wf1/execute', {})
    })
  })

  // =========================================================================
  // run
  // =========================================================================

  describe('run()', () => {
    it('calls POST /workflows/run with YAML and params', async () => {
      post.mockResolvedValue({ ok: true, executionId: 'exec-2' })

      const yaml = 'steps:\n  - module: browser.goto'
      await workflowAPI.run(yaml, { url: 'https://test.com' })

      expect(post).toHaveBeenCalledWith('/workflows/run', {
        workflowYaml: yaml,
        params: { url: 'https://test.com' }
      })
    })

    it('includes startStep and endStep when provided', async () => {
      post.mockResolvedValue({ ok: true })

      await workflowAPI.run('yaml', {}, { startStep: 1, endStep: 3 })

      expect(post).toHaveBeenCalledWith('/workflows/run', {
        workflowYaml: 'yaml',
        params: {},
        startStep: 1,
        endStep: 3
      })
    })

    it('includes breakpoints when provided', async () => {
      post.mockResolvedValue({ ok: true })

      await workflowAPI.run('yaml', {}, { breakpoints: ['node_1', 'node_2'] })

      expect(post).toHaveBeenCalledWith('/workflows/run', {
        workflowYaml: 'yaml',
        params: {},
        breakpoints: ['node_1', 'node_2']
      })
    })

    it('does not include breakpoints when array is empty', async () => {
      post.mockResolvedValue({ ok: true })

      await workflowAPI.run('yaml', {}, { breakpoints: [] })

      const payload = post.mock.calls[0][1]
      expect(payload.breakpoints).toBeUndefined()
    })

    it('includes screenshotMode when provided', async () => {
      post.mockResolvedValue({ ok: true })

      await workflowAPI.run('yaml', {}, { screenshotMode: 'all' })

      expect(post).toHaveBeenCalledWith('/workflows/run', {
        workflowYaml: 'yaml',
        params: {},
        screenshotMode: 'all'
      })
    })
  })

  // =========================================================================
  // stepsToVueFlow / vueFlowToSteps
  // =========================================================================

  describe('stepsToVueFlow()', () => {
    it('calls POST /workflows/steps-to-vueflow', async () => {
      post.mockResolvedValue({ ok: true, nodes: [], edges: [] })

      await workflowAPI.stepsToVueFlow({ steps: [{ module: 'a' }] })

      expect(post).toHaveBeenCalledWith('/workflows/steps-to-vueflow', { steps: [{ module: 'a' }] })
    })
  })

  describe('vueFlowToSteps()', () => {
    it('calls POST /workflows/vueflow-to-steps', async () => {
      post.mockResolvedValue({ ok: true, steps: [] })

      await workflowAPI.vueFlowToSteps({ nodes: [], edges: [] })

      expect(post).toHaveBeenCalledWith('/workflows/vueflow-to-steps', { nodes: [], edges: [] })
    })
  })

  // =========================================================================
  // validate
  // =========================================================================

  describe('validate()', () => {
    it('calls POST /workflows/validate', async () => {
      post.mockResolvedValue({ valid: true, errors: [], warnings: [] })

      const result = await workflowAPI.validate({ steps: [] })

      expect(post).toHaveBeenCalledWith('/workflows/validate', { steps: [] })
      expect(result.valid).toBe(true)
    })
  })

  // =========================================================================
  // computeLayout / computeGraphRelations
  // =========================================================================

  describe('computeLayout()', () => {
    it('calls POST /workflows/layout', async () => {
      post.mockResolvedValue({ ok: true, positions: {} })

      await workflowAPI.computeLayout({ nodes: [], edges: [] })

      expect(post).toHaveBeenCalledWith('/workflows/layout', { nodes: [], edges: [] })
    })
  })

  describe('computeGraphRelations()', () => {
    it('calls POST /workflows/graph-relations', async () => {
      post.mockResolvedValue({ ok: true, relations: {} })

      await workflowAPI.computeGraphRelations({ nodes: [], edges: [] })

      expect(post).toHaveBeenCalledWith('/workflows/graph-relations', { nodes: [], edges: [] })
    })
  })
})

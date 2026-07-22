import { describe, expect, it } from 'vitest'
import {
  auditChecks,
  clientConfigurations,
  createMcpStarter,
  initialArguments,
  normalizeMcpStatus,
  parseArguments,
  sanitizeToolName,
  schemaFields,
  toolSource,
} from '@/features/mcp/studioModel'

const tool = {
  name: 'audit_project',
  inputSchema: {
    type: 'object',
    required: ['target'],
    properties: {
      target: { type: 'string', description: 'Repository path' },
      retries: { type: 'integer', default: 2 },
      strict: { type: 'boolean' },
      labels: { type: 'array' },
      options: { type: 'object' },
    },
  },
  _meta: {
    'flyto2/source': { type: 'workflow', id: 'wf-1', name: 'Audit project' },
  },
}

describe('MCP Studio model', () => {
  it('normalizes sparse status payloads', () => {
    expect(normalizeMcpStatus(null)).toMatchObject({
      ok: false,
      name: 'flyto2-flow',
      transport: 'streamable-http',
      exposedToolCount: 0,
      tools: [],
    })
  })

  it('builds schema-driven form fields and defaults', () => {
    expect(schemaFields(tool).find(field => field.name === 'target')).toMatchObject({ required: true })
    expect(initialArguments(tool)).toEqual({
      target: '', retries: 2, strict: false, labels: '[]', options: '{}',
    })
  })

  it('parses typed arguments', () => {
    expect(parseArguments(tool, {
      target: 'repo', retries: '3', strict: true, labels: '["security"]', options: '{"deep":true}',
    })).toEqual({
      target: 'repo', retries: 3, strict: true, labels: ['security'], options: { deep: true },
    })
  })

  it('rejects missing required and malformed structured inputs', () => {
    expect(() => parseArguments(tool, { target: '' })).toThrow('target is required')
    expect(() => parseArguments(tool, { target: 'repo', labels: '{}' })).toThrow('valid JSON array')
  })

  it('exports portable client configurations without changing runtime auth', () => {
    const configs = clientConfigurations({
      ok: true,
      name: 'flyto-workflows',
      serverUrl: 'https://cloud.example/api/mcp',
      setup: {
        serverName: 'flyto-workflows',
        http: {
          url: 'https://cloud.example/api/mcp',
          headers: { Authorization: 'Bearer <token>' },
        },
        codexToml: '[mcp_servers.flyto-workflows]',
      },
    })

    expect(configs.find(item => item.id === 'codex').content).toContain('mcp_servers')
    expect(configs.find(item => item.id === 'desktop').content).toContain('Bearer <token>')
  })

  it('reports transport, schema, and access audit state', () => {
    const checks = auditChecks({
      ok: true,
      transport: 'streamable-http',
      auth: { localLoopbackAccountless: true },
      tools: [tool],
    })
    expect(checks).toHaveLength(4)
    expect(checks.every(check => check.pass)).toBe(true)
  })

  it('creates an editable MCP workflow starter and exposes its source', () => {
    const starter = createMcpStarter(4)
    expect(starter.steps[0].params).toMatchObject({
      trigger_type: 'mcp',
      tool_name: 'my_mcp_tool_4',
    })
    expect(sanitizeToolName(' Review Project! ')).toBe('review_project')
    expect(toolSource(tool)).toEqual({ type: 'workflow', id: 'wf-1', name: 'Audit project' })
  })
})

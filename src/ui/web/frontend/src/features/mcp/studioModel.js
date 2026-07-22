const SAFE_NAME = /[^a-z0-9_]+/g

export function normalizeMcpStatus(value) {
  const source = value && typeof value === 'object' ? value : {}
  const tools = Array.isArray(source.tools) ? source.tools.filter(Boolean) : []
  return {
    ...source,
    ok: source.ok === true,
    name: source.name || 'flyto2-flow',
    title: source.title || 'Flyto2 Workflow Tools',
    transport: source.transport || 'streamable-http',
    serverUrl: source.serverUrl || source.endpoint || '/api/mcp',
    protocolVersions: Array.isArray(source.protocolVersions) ? source.protocolVersions : [],
    auth: source.auth && typeof source.auth === 'object' ? source.auth : {},
    setup: source.setup && typeof source.setup === 'object' ? source.setup : {},
    tools,
    exposedToolCount: Number.isFinite(source.exposedToolCount)
      ? source.exposedToolCount
      : tools.length,
  }
}
export function toolSource(tool) {
  const source = tool?._meta?.['flyto2/source']
  return source && typeof source === 'object' ? source : {}
}

export function schemaFields(tool) {
  const schema = tool?.inputSchema && typeof tool.inputSchema === 'object'
    ? tool.inputSchema
    : {}
  const properties = schema.properties && typeof schema.properties === 'object'
    ? schema.properties
    : {}
  const required = new Set(Array.isArray(schema.required) ? schema.required : [])
  return Object.entries(properties).map(([name, definition]) => ({
    name,
    type: definition?.type || 'string',
    description: definition?.description || '',
    defaultValue: definition?.default,
    required: required.has(name),
    enumValues: Array.isArray(definition?.enum) ? definition.enum : [],
  }))
}

export function initialArguments(tool) {
  return Object.fromEntries(schemaFields(tool).map(field => {
    if (field.defaultValue !== undefined) return [field.name, field.defaultValue]
    if (field.type === 'boolean') return [field.name, false]
    if (field.type === 'number' || field.type === 'integer') return [field.name, '']
    if (field.type === 'object') return [field.name, '{}']
    if (field.type === 'array') return [field.name, '[]']
    return [field.name, '']
  }))
}

export function parseArguments(tool, values) {
  const output = {}
  for (const field of schemaFields(tool)) {
    const raw = values?.[field.name]
    const empty = raw === '' || raw === undefined || raw === null
    if (empty && field.required) throw new Error(`${field.name} is required`)
    if (empty) continue

    if (field.type === 'number' || field.type === 'integer') {
      const number = Number(raw)
      if (!Number.isFinite(number)) throw new Error(`${field.name} must be a number`)
      output[field.name] = field.type === 'integer' ? Math.trunc(number) : number
      continue
    }
    if (field.type === 'boolean') {
      output[field.name] = raw === true || raw === 'true'
      continue
    }
    if (field.type === 'object' || field.type === 'array') {
      try {
        const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
        if (field.type === 'array' && !Array.isArray(parsed)) throw new Error('array required')
        if (field.type === 'object' && (Array.isArray(parsed) || !parsed || typeof parsed !== 'object')) {
          throw new Error('object required')
        }
        output[field.name] = parsed
      } catch {
        throw new Error(`${field.name} must be valid JSON ${field.type}`)
      }
      continue
    }
    output[field.name] = String(raw)
  }
  return output
}

export function clientConfigurations(statusValue) {
  const status = normalizeMcpStatus(statusValue)
  const serverName = status.setup.serverName || status.name
  const http = status.setup.http || { url: status.serverUrl }
  const jsonEntry = {
    mcpServers: {
      [serverName]: {
        type: 'streamable-http',
        url: http.url || status.serverUrl,
        ...(http.headers ? { headers: http.headers } : {}),
      },
    },
  }
  return [
    {
      id: 'codex',
      label: 'Codex',
      format: 'TOML',
      content: status.setup.codexToml || '',
    },
    {
      id: 'claude-code',
      label: 'Claude Code',
      format: 'JSON',
      content: JSON.stringify(status.setup.claudeCode || jsonEntry, null, 2),
    },
    {
      id: 'desktop',
      label: 'Desktop clients',
      format: 'JSON',
      content: JSON.stringify(jsonEntry, null, 2),
    },
    {
      id: 'http',
      label: 'Streamable HTTP',
      format: 'URL',
      content: http.url || status.serverUrl,
    },
  ]
}

export function auditChecks(statusValue) {
  const status = normalizeMcpStatus(statusValue)
  const schemasValid = status.tools.every(tool => (
    tool.inputSchema?.type === 'object' &&
    tool.inputSchema.properties &&
    typeof tool.inputSchema.properties === 'object'
  ))
  return [
    { id: 'endpoint', label: 'Endpoint reachable', pass: status.ok },
    { id: 'transport', label: 'Streamable HTTP', pass: status.transport === 'streamable-http' },
    { id: 'schema', label: 'Tool schemas valid', pass: schemasValid },
    {
      id: 'access',
      label: status.auth.localLoopbackAccountless ? 'Local-only default' : 'Bearer access',
      pass: status.auth.localLoopbackAccountless === true || status.auth.required === true,
    },
  ]
}

export function starterToolName(index = 1) {
  return `my_mcp_tool_${Math.max(1, Number(index) || 1)}`
}

export function sanitizeToolName(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '_')
    .replace(SAFE_NAME, '')
    .replace(/^_+|_+$/g, '')
}

export function createMcpStarter(index = 1) {
  const toolName = starterToolName(index)
  return {
    name: `MCP Tool ${Math.max(1, Number(index) || 1)}`,
    description: `Callable workflow tool: ${toolName}`,
    category: 'automation',
    tags: ['mcp', 'agent-tool'],
    steps: [
      {
        id: 'mcp_trigger',
        module: 'flow.trigger',
        params: {
          trigger_type: 'mcp',
          tool_name: toolName,
          tool_description: `Run ${toolName}`,
          config: { input_fields: [] },
        },
      },
    ],
    ui: { sections: [] },
  }
}

import { get, post } from '@/api/client'

function normalizeMcpError(error, fallback) {
  const message = String(error || '')
  if (/503|Backend unavailable|Network Error|ECONNREFUSED|Failed to fetch/i.test(message)) {
    return `${fallback}. Start the API or retry after the runtime is healthy.`
  }
  return message || fallback
}
export async function getMcpStatus() {
  try {
    const result = await get('/mcp/status')
    if (!result.ok) {
      return {
        ...result,
        ok: false,
        error: normalizeMcpError(result.toolsError || result.error, 'MCP status unavailable'),
      }
    }
    return result
  } catch (error) {
    return {
      ok: false,
      tools: [],
      exposedToolCount: 0,
      error: normalizeMcpError(error.message, 'MCP status unavailable'),
    }
  }
}

export async function callMcpTool(name, args = {}) {
  try {
    const result = await post(
      '/mcp',
      {
        jsonrpc: '2.0',
        id: `studio-${Date.now()}`,
        method: 'tools/call',
        params: { name, arguments: args },
      },
      { headers: { Accept: 'application/json, text/event-stream' } },
    )
    if (result?.error) {
      return { ok: false, error: result.error.message || 'Tool call failed', response: result }
    }
    return { ok: result?.result?.isError !== true, response: result, result: result?.result }
  } catch (error) {
    return { ok: false, error: normalizeMcpError(error.message, 'Tool call failed') }
  }
}

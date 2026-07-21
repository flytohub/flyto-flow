import { get } from '@/api/client'

function normalizeMcpError(error, fallback) {
  const message = String(error || '')
  if (/503|Backend unavailable|Network Error|ECONNREFUSED|Failed to fetch/i.test(message)) {
    return `${fallback}. Start the cloud API or try again after the backend is healthy.`
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
  } catch (err) {
    return {
      ok: false,
      tools: [],
      exposedToolCount: 0,
      error: normalizeMcpError(err.message, 'MCP status unavailable'),
    }
  }
}

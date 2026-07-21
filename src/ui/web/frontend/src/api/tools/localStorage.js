/**
 * Tools Local Storage Fallback
 *
 * Provides offline CRUD operations using localStorage
 * when the backend API is unavailable.
 */

const STORAGE_KEY = 'flyto_tools'

/** Generate a unique tool ID using timestamp and random suffix */
export function generateId() {
  return `tool_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`
}

function _readAll() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch {
    return []
  }
}

function _writeAll(tools) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tools))
}

/** Get all tools from localStorage */
export function getToolsFromLocal() {
  return { ok: true, tools: _readAll() }
}

/** Get a single tool by ID from localStorage */
export function getToolFromLocal(toolId) {
  const tools = _readAll()
  const tool = tools.find(t => t.id === toolId)
  return tool ? { ok: true, tool } : { ok: false, error: 'Tool not found' }
}

/** Save a new tool to localStorage */
export function saveToolToLocal(tool) {
  const tools = _readAll()
  const newTool = { ...tool, id: tool.id || generateId(), createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() }
  tools.push(newTool)
  _writeAll(tools)
  return { ok: true, tool: newTool }
}

/** Update an existing tool in localStorage by ID */
export function updateToolInLocal(toolId, updates) {
  const tools = _readAll()
  const idx = tools.findIndex(t => t.id === toolId)
  if (idx === -1) return { ok: false, error: 'Tool not found' }
  tools[idx] = { ...tools[idx], ...updates, updatedAt: new Date().toISOString() }
  _writeAll(tools)
  return { ok: true, tool: tools[idx] }
}

/** Delete a tool from localStorage by ID */
export function deleteToolFromLocal(toolId) {
  const tools = _readAll()
  _writeAll(tools.filter(t => t.id !== toolId))
  return { ok: true }
}

/** Search tools in localStorage by name or description */
export function searchToolsLocal(query, filters = {}) {
  const tools = _readAll()
  const q = (query || '').toLowerCase()
  const filtered = tools.filter(t => {
    const name = (t.meta?.name || t.name || '').toLowerCase()
    const desc = (t.meta?.description || t.description || '').toLowerCase()
    return name.includes(q) || desc.includes(q)
  })
  return { ok: true, tools: filtered }
}

/** Get the list of default tool categories */
export function getDefaultCategories() {
  return { ok: true, categories: ['HTTP', 'Database', 'File', 'Text', 'Custom'] }
}

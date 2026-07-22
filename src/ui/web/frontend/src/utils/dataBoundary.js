/**
 * Small frontend data-boundary helpers.
 *
 * Keep API/store hydration stable when initial data is null, partial, stale, or
 * still crossing the loading boundary.
 */

export function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

export function asObject(value) {
  return isPlainObject(value) ? value : {}
}

export function asArray(value) {
  return Array.isArray(value) ? value : []
}

export function asRecordArray(value) {
  return asArray(value).filter(isPlainObject)
}

export function asString(value, fallback = '') {
  return typeof value === 'string' ? value : fallback
}

export function asBoolean(value, fallback = false) {
  return typeof value === 'boolean' ? value : fallback
}

export function asNumber(value, fallback = 0) {
  return Number.isFinite(value) ? value : fallback
}

export function asInteger(value, fallback = 0) {
  const number = Number(value)
  return Number.isInteger(number) ? number : fallback
}

export function asNonNegativeInteger(value, fallback = 0) {
  return Math.max(0, asInteger(value, fallback))
}

export function pickFirst(source, keys, fallback = undefined) {
  const obj = asObject(source)
  for (const key of keys) {
    if (obj[key] !== undefined && obj[key] !== null) {
      return obj[key]
    }
  }
  return fallback
}

export function pickArray(source, keys) {
  return asArray(pickFirst(source, keys, []))
}

export function pickObject(source, keys) {
  return asObject(pickFirst(source, keys, {}))
}

export function pickString(source, keys, fallback = '') {
  return asString(pickFirst(source, keys, fallback), fallback)
}

export function pickBoolean(source, keys, fallback = false) {
  return asBoolean(pickFirst(source, keys, fallback), fallback)
}

export function pickNumber(source, keys, fallback = 0) {
  return asNumber(pickFirst(source, keys, fallback), fallback)
}

export function pickInteger(source, keys, fallback = 0) {
  return asInteger(pickFirst(source, keys, fallback), fallback)
}

export function hasRecords(value) {
  return asRecordArray(value).length > 0
}

export function cloneBoundaryValue(value, fallback = {}) {
  try {
    return JSON.parse(JSON.stringify(value ?? fallback))
  } catch {
    if (Array.isArray(fallback)) return [...fallback]
    if (isPlainObject(fallback)) return { ...fallback }
    return fallback
  }
}

export function normalizeOkEnvelope(payload) {
  const raw = asObject(payload)
  return {
    ok: raw.ok !== false,
    error: asString(raw.error || raw.message, ''),
    raw
  }
}

export function normalizeListEnvelope(payload, listKeys = ['items'], options = {}) {
  const raw = asObject(payload)
  const templates = asRecordArray(pickFirst(raw, listKeys, []))
  const page = asNonNegativeInteger(raw.page, options.page ?? 1) || 1
  const pageSize = asNonNegativeInteger(raw.pageSize ?? raw.page_size, options.pageSize ?? templates.length)
  const total = asNonNegativeInteger(raw.total ?? raw.totalCount ?? raw.total_count, templates.length)
  return {
    ok: raw.ok !== false,
    items: templates,
    total,
    totalCount: total,
    page,
    pageSize,
    hasNext: asBoolean(raw.hasNext ?? raw.has_next, pageSize > 0 ? page * pageSize < total : false),
    error: asString(raw.error || raw.message, ''),
    raw
  }
}

export function normalizeTieredCatalogResponse(response) {
  const raw = asObject(response)
  const defaultBucket = asObject(raw.default)
  const expertBucket = asObject(raw.expert)

  return {
    defaultModules: asRecordArray(defaultBucket.modules ?? raw.defaultModules),
    expertModules: asRecordArray(expertBucket.modules ?? raw.expertModules),
    modulesByCategory: pickObject(raw, ['modulesByCategory', 'modules_by_category']),
    moduleCategories: pickArray(raw, ['moduleCategories', 'module_categories']),
    modulesMetadata: pickObject(raw, ['modulesMetadata', 'modules_metadata']),
    version: asString(raw.version, '')
  }
}

export function normalizeTemplateListResponse(result) {
  if (Array.isArray(result)) {
    const templates = asRecordArray(result)
    return {
      ok: true,
      templates,
      enabledCount: templates.length,
      totalCount: templates.length,
      raw: result
    }
  }

  const raw = asObject(result)
  const templates = asRecordArray(raw.templates)
  return {
    ok: raw.ok !== false,
    templates,
    enabledCount: asNumber(raw.enabledCount ?? raw.enabled_count, templates.length),
    totalCount: asNumber(raw.totalCount ?? raw.total_count, templates.length),
    error: asString(raw.error || raw.message, ''),
    raw
  }
}

export function normalizeWorkflowListResponse(result) {
  const normalized = normalizeListEnvelope(result, ['workflows', 'items'], {
    page: 1,
    pageSize: 0
  })
  return {
    ...normalized,
    workflows: normalized.items,
    enabledCount: asNonNegativeInteger(asObject(result).enabledCount ?? asObject(result).enabled_count, normalized.items.length),
    totalCount: asNonNegativeInteger(asObject(result).totalCount ?? asObject(result).total_count, normalized.totalCount)
  }
}

export function normalizeWorkflowPayload(workflow) {
  const raw = asObject(workflow)
  return Object.keys(raw).length > 0 ? raw : null
}

export function normalizeTemplatePayload(template) {
  const raw = asObject(template)
  return {
    id: asString(raw.id, ''),
    templateName: asString(raw.templateName || raw.template_name || raw.name, ''),
    templateId: asString(raw.templateId || raw.template_id || raw.id, 'new_template'),
    templateDescription: asString(raw.templateDescription || raw.template_description || raw.description, ''),
    sections: asArray(raw.ui?.sections)
  }
}

export function normalizeRecordingStopResponse(result) {
  const raw = asObject(result)
  const steps = asRecordArray(raw.steps)
  const warnings = asRecordArray(raw.warnings).map(warning => ({
    ...warning,
    code: asString(warning.code, 'recording_warning'),
    message: asString(warning.message, ''),
  })).filter(warning => warning.message)
  const summary = asObject(raw.recordingSummary ?? raw.recording_summary)
  return {
    ok: raw.ok !== false,
    workflowResult: Object.keys(raw).length > 0 ? raw : null,
    steps,
    compiledSteps: raw.ok === false ? null : steps,
    recordingSummary: Object.keys(summary).length > 0 ? summary : null,
    warnings,
    error: asString(raw.error || raw.message, '')
  }
}


export function normalizeWorkflowElements(elements) {
  return asRecordArray(elements).reduce((acc, element) => {
    if (element.source && element.target) {
      acc.edges.push(element)
    } else if (element.id) {
      acc.nodes.push(element)
    }
    return acc
  }, { nodes: [], edges: [] })
}

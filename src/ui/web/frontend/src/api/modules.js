/**
 * Modules API
 * Dynamic module catalog from backend
 */

import { get } from './client'

/**
 * Get single module metadata
 */
export async function getModule(moduleId, lang = 'en') {
  return await get(`/modules/${moduleId}?lang=${lang}`)
}

/**
 * Get tiered module catalog
 * Returns all modules (default + expert) with metadata
 */
export async function getTieredCatalog({
  lang = 'en',
  includeExpert = true,
  includeTemplates = true,
  forceRefresh = false,
  excludeTemplateId = null
} = {}) {
  const params = new URLSearchParams({
    lang,
    include_expert: includeExpert,
    include_templates: includeTemplates,
    skip_access_control: true
  })

  if (excludeTemplateId) {
    params.append('exclude_template_id', excludeTemplateId)
  }

  return await get(`/modules/tiered?${params}`)
}

/**
 * Validate if two modules can be connected
 */
export async function validateConnection(source, target, context = [], sourcePort = null, targetPort = null) {
  const params = new URLSearchParams({ source, target })
  if (sourcePort) params.append('source_port', sourcePort)
  if (targetPort) params.append('target_port', targetPort)
  if (context.length > 0) {
    params.append('context', context.join(','))
  }
  return await get(`/modules/validate-connection?${params}`)
}

/**
 * Validate if a module can be inserted between two modules
 */
export async function validateInsertion(source, target, downstream, sourcePort = 'output', targetPort = 'input') {
  const params = new URLSearchParams({ source, target, downstream, source_port: sourcePort, target_port: targetPort })
  return await get(`/modules/validate-insertion?${params}`)
}

/**
 * Get modules that can be used as workflow starters
 */
export async function getStarterModules(includeComposites = true) {
  const params = new URLSearchParams({ includeComposites })
  const response = await get(`/modules/starters?${params}`)

  if (response.modules) {
    response.modules = response.modules.map(m => ({
      ...m,
      moduleId: m.module_id || m.moduleId,
      startRequiresParams: m.start_requires_params || m.startRequiresParams || []
    }))
  }

  return response
}

/**
 * Get compatible modules for node replacement
 */
export async function getConnectableForReplacement({
  upstreamModule = null,
  downstreamModule = null,
  limit = 200
} = {}) {
  const params = new URLSearchParams({ limit })
  if (upstreamModule) params.append('upstream_module', upstreamModule)
  if (downstreamModule) params.append('downstream_module', downstreamModule)
  return await get(`/modules/connectable-for-replacement?${params}`)
}

/**
 * Get connectable modules for a given module
 */
export async function getConnectableModules(moduleId, {
  direction = 'next',
  search = null,
  category = null
} = {}) {
  const params = new URLSearchParams({
    module_id: moduleId,
    direction
  })
  if (search) params.append('search', search)
  if (category) params.append('category', category)
  return await get(`/modules/connectable?${params}`)
}

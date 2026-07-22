/** Normalize the local SQLite template DTO for the visual builder. */
export function normalizeTemplate(data = {}, id = null) {
  const workflow = data.workflowData || data.workflow_data || {}
  const ui = data.ui || workflow.ui || null
  return {
    id: id || data.id,
    name: data.name || 'Untitled workflow',
    templateName: data.name || 'Untitled workflow',
    description: data.description || '',
    templateDescription: data.description || '',
    category: data.category || 'general',
    tags: data.tags || [],
    steps: data.steps || workflow.steps || [],
    ui,
    iconUrl: data.iconUrl || data.icon_url || ui?.templateIcon || '',
    viewport: ui?.viewport || null,
    checkpoints: data.checkpoints || workflow.checkpoints || [],
    error_workflow_id: data.errorWorkflowId || data.error_workflow_id || workflow.error_workflow_id || null,
    error_handling: data.errorHandling || data.error_handling || workflow.error_handling || null,
    createdAt: data.createdAt || data.created_at || null,
    updatedAt: data.updatedAt || data.updated_at || null,
    capabilities: { execute: true, edit: true, delete: true },
  }
}

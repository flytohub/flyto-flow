/**
 * Auto Layout - Public API
 *
 * @example
 * import { useAutoLayout } from '@/composables/workflowEditor/canvasOps/autoLayout'
 * const { layout, compact } = useAutoLayout()
 * const newNodes = await layout(nodes, edges)
 */

export { useAutoLayout, PRESETS } from './autoLayout/useAutoLayout'

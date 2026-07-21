/**
 * Trigger Node - Workflow Entry Point
 *
 * Trigger types:
 * - manual: User-initiated execution
 * - webhook: HTTP webhook call
 * - schedule: Cron-based schedule
 * - event: Internal or external event
 *
 * 5-Star: Handles defined in backend node_config.py
 */
export default {
  type: 'trigger',

  // Default parameters
  getDefaultParams: () => ({
    triggerType: 'manual',
    webhookPath: '',
    schedule: '',
    eventName: '',
    description: ''
  }),

  // Style
  styleClass: 'trigger-node',
  isFlowControl: true,

  // Trigger-specific flag
  isTrigger: true,

  // Entry point flag
  isEntryPoint: true,

  // Parameter editor component
  paramsComponent: 'TriggerParams',

  // Show add button after trigger
  showAddButton: true,

  // Helper to get trigger type icon
  getTriggerIcon: (params) => {
    const icons = {
      manual: 'Hand',
      webhook: 'Webhook',
      schedule: 'Clock',
      event: 'Zap'
    }
    return icons[params?.triggerType] || 'Zap'
  }
}

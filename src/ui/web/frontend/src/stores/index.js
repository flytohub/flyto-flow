/**
 * Pinia Stores unified exports
 */

// Individual Stores
export { useUserStore } from './userStore'
export { useTemplateStore } from './templateStore'
export { useWorkflowStore } from './workflowStore'
export { useBuilderStore } from './builderStore'
export { useModulesStore } from './modulesStore'
export { useCapabilitiesStore } from './capabilitiesStore'
export { useDashboardStore } from './dashboardStore'
// useAdminStore removed — adminStore was deleted when admin moved to flyto-admin;
// this dead re-export of a non-existent file was breaking the production build.
export { usePluginStore } from './pluginStore'

// Phase 8: Observability
export { useMetricsStore } from './metricsStore'
export { useTraceStore } from './traceStore'
export { useAlertStore } from './alertStore'

// Phase 9: Version Control & Audit
export { useAuditStore } from './auditStore'

// Phase 7: Multi-tenancy
export { useOrganizationStore } from './organizationStore'
export { useProjectStore } from './projectStore'
export { useRoleStore } from './roleStore'

// Execution Control (P0)
export { useExecutionControlStore } from './executionControlStore'

// Wallet
export { useWalletStore } from './walletStore'

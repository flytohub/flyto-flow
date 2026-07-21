/**
 * Telemetry Event Constants
 *
 * Centralized event definitions for analytics tracking.
 * All event names and property schemas are defined here to ensure consistency.
 *
 * Naming Convention: {category}.{action}
 * - category: The feature area (auth, template, workflow, etc.)
 * - action: The specific action (create, delete, view, etc.)
 */

// ============================================================================
// AUTH EVENTS
// ============================================================================
export const AUTH_EVENTS = {
  LOGIN: 'auth.login',
  LOGOUT: 'auth.logout',
  REGISTER: 'auth.register',
  PASSWORD_RESET: 'auth.password_reset',
  SESSION_EXPIRE: 'auth.session_expire',
}

// ============================================================================
// TEMPLATE EVENTS
// ============================================================================
export const TEMPLATE_EVENTS = {
  CREATE: 'template.create',
  SAVE: 'template.save',
  DELETE: 'template.delete',
  PUBLISH: 'template.publish',
  UNPUBLISH: 'template.unpublish',
  DUPLICATE: 'template.duplicate',
  IMPORT: 'template.import',
  EXPORT: 'template.export',
}

// ============================================================================
// WORKFLOW EVENTS
// ============================================================================
export const WORKFLOW_EVENTS = {
  EXECUTE_START: 'workflow.execute_start',
  EXECUTE_COMPLETE: 'workflow.execute_complete',
  EXECUTE_ERROR: 'workflow.execute_error',
  EXECUTE_CANCEL: 'workflow.execute_cancel',
}

// ============================================================================
// EXECUTION CONTROL EVENTS
// ============================================================================
export const EXECUTION_EVENTS = {
  PAUSE: 'execution.pause',
  RESUME: 'execution.resume',
  STEP: 'execution.step',
  RESUME_FROM_CHECKPOINT: 'execution.resume_from_checkpoint',
  CHECKPOINT_CONTINUE: 'execution.checkpoint_continue',
  CHECKPOINT_BYPASS: 'execution.checkpoint_bypass',
}

// ============================================================================
// BUILDER EVENTS
// ============================================================================
export const BUILDER_EVENTS = {
  // Session
  SESSION_START: 'builder.session_start',
  SESSION_END: 'builder.session_end',

  // Node operations
  NODE_ADD: 'builder.node_add',
  NODE_DELETE: 'builder.node_delete',
  NODE_CONNECT: 'builder.node_connect',
  NODE_DISCONNECT: 'builder.node_disconnect',
  NODE_CONFIGURE: 'builder.node_configure',
  NODE_COPY: 'builder.node_copy',
  NODE_PASTE: 'builder.node_paste',

  // Canvas operations
  UNDO: 'builder.undo',
  REDO: 'builder.redo',
  ZOOM: 'builder.zoom',
  FIT_VIEW: 'builder.fit_view',

  // Testing
  TEST_RUN: 'builder.test_run',
  DEBUG_TOGGLE: 'builder.debug_toggle',
}

// ============================================================================
// MARKETPLACE EVENTS
// ============================================================================
export const MARKETPLACE_EVENTS = {
  // Discovery
  SEARCH: 'marketplace.search',
  FILTER: 'marketplace.filter',
  SORT: 'marketplace.sort',

  // Template interaction
  VIEW_TEMPLATE: 'marketplace.view_template',
  PREVIEW_TEMPLATE: 'marketplace.preview_template',

  // Library actions
  INSTALL: 'marketplace.install',
  UNINSTALL: 'marketplace.uninstall',

  // Purchase funnel
  PURCHASE_START: 'marketplace.purchase_start',
  PURCHASE_COMPLETE: 'marketplace.purchase_complete',
  PURCHASE_ABANDON: 'marketplace.purchase_abandon',

  // Other actions
  FAVORITE_ADD: 'marketplace.favorite_add',
  FAVORITE_REMOVE: 'marketplace.favorite_remove',
  SHARE: 'marketplace.share',
  REPORT: 'marketplace.report',
}

// ============================================================================
// AI ASSISTANT EVENTS
// ============================================================================
export const AI_EVENTS = {
  // Chat
  CHAT_OPEN: 'ai.chat_open',
  CHAT_CLOSE: 'ai.chat_close',
  MESSAGE_SEND: 'ai.message_send',
  MESSAGE_RECEIVE: 'ai.message_receive',

  // Suggestions
  SUGGESTION_SHOW: 'ai.suggestion_show',
  SUGGESTION_ACCEPT: 'ai.suggestion_accept',
  SUGGESTION_REJECT: 'ai.suggestion_reject',
  SUGGESTION_MODIFY: 'ai.suggestion_modify',

  // Workflow generation
  WORKFLOW_GENERATE_START: 'ai.workflow_generate_start',
  WORKFLOW_GENERATE_COMPLETE: 'ai.workflow_generate_complete',
  WORKFLOW_GENERATE_ERROR: 'ai.workflow_generate_error',
  WORKFLOW_APPLY: 'ai.workflow_apply',

  // Feedback
  FEEDBACK_POSITIVE: 'ai.feedback_positive',
  FEEDBACK_NEGATIVE: 'ai.feedback_negative',
}

// ============================================================================
// CHAT EVENTS (User-to-user messaging)
// ============================================================================
export const CHAT_EVENTS = {
  CONVERSATION_START: 'chat.conversation_start',
  SEND_MESSAGE: 'chat.send_message',
  FILE_UPLOAD: 'chat.file_upload',
  MARK_READ: 'chat.mark_read',
}

// ============================================================================
// VARIABLE & CREDENTIAL EVENTS
// ============================================================================
export const VARIABLE_EVENTS = {
  CREATE: 'variable.create',
  UPDATE: 'variable.update',
  DELETE: 'variable.delete',
}

export const CREDENTIAL_EVENTS = {
  CREATE: 'credential.create',
  DELETE: 'credential.delete',
  REVEAL: 'credential.reveal',
}

// ============================================================================
// TRIGGER EVENTS
// ============================================================================
export const TRIGGER_EVENTS = {
  SCHEDULE_CREATE: 'schedule.create',
  SCHEDULE_UPDATE: 'schedule.update',
  SCHEDULE_DELETE: 'schedule.delete',
  SCHEDULE_TOGGLE: 'schedule.toggle',

  WEBHOOK_CREATE: 'webhook.create',
  WEBHOOK_DELETE: 'webhook.delete',
  WEBHOOK_REGENERATE: 'webhook.regenerate',
}

// ============================================================================
// ALERT EVENTS
// ============================================================================
export const ALERT_EVENTS = {
  ACKNOWLEDGE: 'alert.acknowledge',
  DISMISS: 'alert.dismiss',
  RULE_CREATE: 'alert_rule.create',
  RULE_UPDATE: 'alert_rule.update',
  RULE_DELETE: 'alert_rule.delete',
}

// ============================================================================
// PLUGIN EVENTS
// ============================================================================
export const PLUGIN_EVENTS = {
  SEARCH: 'plugin.search',
  VIEW: 'plugin.view',
  INSTALL: 'plugin.install',
  UNINSTALL: 'plugin.uninstall',
  UPDATE: 'plugin.update',
}

// ============================================================================
// ORGANIZATION EVENTS
// ============================================================================
export const ORGANIZATION_EVENTS = {
  CREATE: 'organization.create',
  UPDATE: 'organization.update',
  DELETE: 'organization.delete',

  MEMBER_INVITE: 'organization.member_invite',
  MEMBER_REMOVE: 'organization.member_remove',
  MEMBER_ROLE_UPDATE: 'organization.member_role_update',
  MEMBER_ACCEPT_INVITE: 'organization.member_accept_invite',
}

// ============================================================================
// PROJECT EVENTS
// ============================================================================
export const PROJECT_EVENTS = {
  CREATE: 'project.create',
  UPDATE: 'project.update',
  DELETE: 'project.delete',
  ARCHIVE: 'project.archive',
  MEMBER_ADD: 'project.member_add',
  MEMBER_REMOVE: 'project.member_remove',
}

// ============================================================================
// MODULE EVENTS
// ============================================================================
export const MODULE_EVENTS = {
  CATALOG_LOAD: 'modules.catalog_load',
  SEARCH: 'modules.search',
  VIEW_DETAILS: 'modules.view_details',
  SELECT: 'modules.select',
}

// ============================================================================
// DASHBOARD EVENTS
// ============================================================================
export const DASHBOARD_EVENTS = {
  LOAD: 'dashboard.load',
  WIDGET_INTERACT: 'dashboard.widget_interact',
  DATE_RANGE_CHANGE: 'dashboard.date_range_change',
  EXPORT_REPORT: 'dashboard.export_report',
}

// ============================================================================
// UX FRICTION EVENTS
// ============================================================================
export const UX_EVENTS = {
  // Validation
  VALIDATION_ERROR: 'ux.validation_error',
  FORM_ABANDON: 'ux.form_abandon',

  // Permissions
  PERMISSION_DENIED: 'ux.permission_denied',
  FEATURE_LOCKED: 'ux.feature_locked',

  // Limits
  QUOTA_WARNING: 'ux.quota_warning',
  QUOTA_EXCEEDED: 'ux.quota_exceeded',

  // Errors
  API_ERROR: 'ux.api_error',
  NETWORK_ERROR: 'ux.network_error',
  TIMEOUT: 'ux.timeout',
}

// ============================================================================
// ACTIVATION & ONBOARDING EVENTS
// ============================================================================
export const ACTIVATION_EVENTS = {
  // Onboarding flow
  ONBOARDING_START: 'activation.onboarding_start',
  ONBOARDING_STEP: 'activation.onboarding_step',
  ONBOARDING_COMPLETE: 'activation.onboarding_complete',
  ONBOARDING_SKIP: 'activation.onboarding_skip',

  // First-time actions (milestones)
  FIRST_TEMPLATE_CREATE: 'activation.first_template_create',
  FIRST_WORKFLOW_EXECUTE: 'activation.first_workflow_execute',
  FIRST_TEMPLATE_PUBLISH: 'activation.first_template_publish',
  FIRST_PURCHASE: 'activation.first_purchase',
  FIRST_SALE: 'activation.first_sale',

  // Feature discovery
  FEATURE_DISCOVER: 'activation.feature_discover',
  TOOLTIP_VIEW: 'activation.tooltip_view',
  HELP_CLICK: 'activation.help_click',
  DOCS_VISIT: 'activation.docs_visit',
}

// ============================================================================
// SETTINGS EVENTS
// ============================================================================
export const SETTINGS_EVENTS = {
  CHANGE: 'settings.change',
  THEME_SWITCH: 'settings.theme_switch',
  LANGUAGE_CHANGE: 'settings.language_change',
  NOTIFICATION_TOGGLE: 'settings.notification_toggle',
}

// ============================================================================
// PAGE EVENTS
// ============================================================================
export const PAGE_EVENTS = {
  VIEW: 'page.view',
  LEAVE: 'page.leave',
  SESSION_START: 'page.session_start',
  SESSION_END: 'page.session_end',
}

// ============================================================================
// SEARCH EVENTS
// ============================================================================
export const SEARCH_EVENTS = {
  QUERY: 'search.query',
  RESULT_CLICK: 'search.result_click',
  NO_RESULTS: 'search.no_results',
  FILTER_APPLY: 'search.filter_apply',
}

// ============================================================================
// TRIAL MODE EVENTS
// ============================================================================
export const TRIAL_EVENTS = {
  // Trial lifecycle
  START: 'trial.start',
  CONTINUE: 'trial.continue',
  ABORT: 'trial.abort',
  COMPLETE: 'trial.complete',

  // Batch events
  BATCH_START: 'trial.batch_start',
  BATCH_COMPLETE: 'trial.batch_complete',
  BATCH_ERROR: 'trial.batch_error',

  // Approval flow
  WAITING_APPROVAL: 'trial.waiting_approval',
  APPROVED: 'trial.approved',
  REJECTED: 'trial.rejected',

  // Input methods
  CSV_UPLOAD: 'trial.csv_upload',
  MANUAL_INPUT: 'trial.manual_input',
}

// ============================================================================
// EVIDENCE/SCREENSHOT EVENTS
// ============================================================================
export const EVIDENCE_EVENTS = {
  SCREENSHOT_MODE_CHANGE: 'evidence.screenshot_mode_change',
  SCREENSHOT_CAPTURED: 'evidence.screenshot_captured',
  SCREENSHOT_VIEW: 'evidence.screenshot_view',
  EVIDENCE_DOWNLOAD: 'evidence.download',
}

// ============================================================================
// SEGMENT/USER CLASSIFICATION EVENTS
// ============================================================================
export const SEGMENT_EVENTS = {
  // User segment identification
  USER_SEGMENT_IDENTIFIED: 'segment.user_identified',
  USER_TYPE_CLASSIFIED: 'segment.user_type',
  USER_SKILL_LEVEL: 'segment.skill_level',

  // Usage intensity
  USAGE_INTENSITY: 'segment.usage_intensity',

  // Cohort tracking
  SIGNUP_COHORT: 'segment.signup_cohort',
  ACTIVATION_COHORT: 'segment.activation_cohort',
}

// ============================================================================
// PERFORMANCE EVENTS
// ============================================================================
export const PERFORMANCE_EVENTS = {
  // API performance
  SLOW_API: 'performance.slow_api',
  API_TIMEOUT: 'performance.api_timeout',

  // Builder performance
  NODE_DRAG: 'performance.node_drag',
  CANVAS_RENDER: 'performance.canvas_render',
  WORKFLOW_LOAD: 'performance.workflow_load',

  // Page performance
  PAGE_LOAD_SLOW: 'performance.page_load_slow',
  INTERACTION_LATENCY: 'performance.interaction_latency',
}

// ============================================================================
// SESSION QUALITY EVENTS
// ============================================================================
export const SESSION_EVENTS = {
  // Builder session
  SESSION_QUALITY: 'session.quality',
  SESSION_IDLE: 'session.idle',
  SESSION_PRODUCTIVE: 'session.productive',

  // Error recovery
  ERROR_RECOVERY: 'session.error_recovery',
  ERROR_ABANDON: 'session.error_abandon',
}

// ============================================================================
// APP LIFECYCLE EVENTS (Desktop only)
// ============================================================================
export const APP_EVENTS = {
  LAUNCH: 'app.launch',
  UPDATE_AVAILABLE: 'app.update_available',
  UPDATE_INSTALLED: 'app.update_installed',
  UPDATE_FAILED: 'app.update_failed',
}

// ============================================================================
// EXPORT ALL EVENTS
// ============================================================================
export const TELEMETRY_EVENTS = {
  APP: APP_EVENTS,
  AUTH: AUTH_EVENTS,
  TEMPLATE: TEMPLATE_EVENTS,
  WORKFLOW: WORKFLOW_EVENTS,
  EXECUTION: EXECUTION_EVENTS,
  BUILDER: BUILDER_EVENTS,
  MARKETPLACE: MARKETPLACE_EVENTS,
  AI: AI_EVENTS,
  CHAT: CHAT_EVENTS,
  VARIABLE: VARIABLE_EVENTS,
  CREDENTIAL: CREDENTIAL_EVENTS,
  TRIGGER: TRIGGER_EVENTS,
  ALERT: ALERT_EVENTS,
  PLUGIN: PLUGIN_EVENTS,
  ORGANIZATION: ORGANIZATION_EVENTS,
  PROJECT: PROJECT_EVENTS,
  MODULE: MODULE_EVENTS,
  DASHBOARD: DASHBOARD_EVENTS,
  UX: UX_EVENTS,
  ACTIVATION: ACTIVATION_EVENTS,
  SETTINGS: SETTINGS_EVENTS,
  PAGE: PAGE_EVENTS,
  SEARCH: SEARCH_EVENTS,
  TRIAL: TRIAL_EVENTS,
  EVIDENCE: EVIDENCE_EVENTS,
  SEGMENT: SEGMENT_EVENTS,
  PERFORMANCE: PERFORMANCE_EVENTS,
  SESSION: SESSION_EVENTS,
}

export default TELEMETRY_EVENTS

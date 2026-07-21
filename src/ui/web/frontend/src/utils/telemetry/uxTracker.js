/**
 * UX Friction Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks UX friction events only.
 */

import { telemetry } from '@/services/telemetry'
import { UX_EVENTS } from '@/constants/telemetryEvents'

export const trackUX = {
  validationError: (formName, fieldName, errorType) => {
    telemetry.track(UX_EVENTS.VALIDATION_ERROR, {
      form_name: formName,
      field_name: fieldName,
      error_type: errorType,
    })
  },

  formAbandon: (formName, lastField, completedPercent) => {
    telemetry.track(UX_EVENTS.FORM_ABANDON, {
      form_name: formName,
      last_field: lastField,
      completed_percent: completedPercent,
    })
  },

  permissionDenied: (feature, requiredRole = null) => {
    telemetry.track(UX_EVENTS.PERMISSION_DENIED, { feature, required_role: requiredRole })
  },

  featureLocked: (feature, requiredPlan = null) => {
    telemetry.track(UX_EVENTS.FEATURE_LOCKED, { feature, required_plan: requiredPlan })
  },

  quotaWarning: (resource, currentUsage, limit) => {
    telemetry.track(UX_EVENTS.QUOTA_WARNING, {
      resource,
      current_usage: currentUsage,
      limit,
    })
  },

  quotaExceeded: (resource, limit) => {
    telemetry.track(UX_EVENTS.QUOTA_EXCEEDED, { resource, limit })
  },

  apiError: (endpoint, statusCode, errorMessage) => {
    telemetry.track(UX_EVENTS.API_ERROR, {
      endpoint,
      status_code: statusCode,
      error_message: errorMessage,
    })
  },

  timeout: (operation, timeoutMs) => {
    telemetry.track(UX_EVENTS.TIMEOUT, { operation, timeout_ms: timeoutMs })
  },
}

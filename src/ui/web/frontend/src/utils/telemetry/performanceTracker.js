/**
 * Performance Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks performance events only.
 */

import { telemetry } from '@/services/telemetry'
import { PERFORMANCE_EVENTS } from '@/constants/telemetryEvents'

export const trackPerformance = {
  slowApi: (endpoint, method, durationMs, statusCode) => {
    telemetry.track(PERFORMANCE_EVENTS.SLOW_API, {
      endpoint,
      method,
      duration_ms: durationMs,
      status_code: statusCode,
    })
  },

  apiTimeout: (endpoint, method, timeoutMs) => {
    telemetry.track(PERFORMANCE_EVENTS.API_TIMEOUT, {
      endpoint,
      method,
      timeout_ms: timeoutMs,
    })
  },

  nodeDrag: (nodeType, durationMs, templateId = null) => {
    telemetry.track(PERFORMANCE_EVENTS.NODE_DRAG, {
      node_type: nodeType,
      duration_ms: durationMs,
      template_id: templateId,
    })
  },

  canvasRender: (nodeCount, durationMs, templateId = null) => {
    telemetry.track(PERFORMANCE_EVENTS.CANVAS_RENDER, {
      node_count: nodeCount,
      duration_ms: durationMs,
      template_id: templateId,
    })
  },

  workflowLoad: (templateId, nodeCount, durationMs) => {
    telemetry.track(PERFORMANCE_EVENTS.WORKFLOW_LOAD, {
      template_id: templateId,
      node_count: nodeCount,
      duration_ms: durationMs,
    })
  },

  pageLoadSlow: (pagePath, durationMs) => {
    telemetry.track(PERFORMANCE_EVENTS.PAGE_LOAD_SLOW, {
      page_path: pagePath,
      duration_ms: durationMs,
    })
  },

  interactionLatency: (actionType, durationMs, context = null) => {
    telemetry.track(PERFORMANCE_EVENTS.INTERACTION_LATENCY, {
      action_type: actionType,
      duration_ms: durationMs,
      context,
    })
  },
}

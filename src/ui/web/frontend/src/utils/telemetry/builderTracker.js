/**
 * Builder Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks builder events only.
 */

import { telemetry } from '@/services/telemetry'
import { BUILDER_EVENTS } from '@/constants/telemetryEvents'
import { sessionState } from './state'

export const trackBuilder = {
  sessionStart: (templateId) => {
    sessionState.builderSessionStart = Date.now()
    sessionState.currentTemplateId = templateId
    telemetry.track(BUILDER_EVENTS.SESSION_START, { template_id: templateId })
  },

  sessionEnd: (templateId = null) => {
    const duration = sessionState.builderSessionStart
      ? Date.now() - sessionState.builderSessionStart
      : null
    telemetry.track(BUILDER_EVENTS.SESSION_END, {
      template_id: templateId || sessionState.currentTemplateId,
      duration_ms: duration,
    })
    sessionState.builderSessionStart = null
    sessionState.currentTemplateId = null
  },

  nodeAdd: (nodeType, templateId = null) => {
    telemetry.track(BUILDER_EVENTS.NODE_ADD, {
      node_type: nodeType,
      template_id: templateId || sessionState.currentTemplateId,
    })
  },

  nodeDelete: (nodeType, templateId = null) => {
    telemetry.track(BUILDER_EVENTS.NODE_DELETE, {
      node_type: nodeType,
      template_id: templateId || sessionState.currentTemplateId,
    })
  },

  nodeConnect: (sourceType, targetType) => {
    telemetry.track(BUILDER_EVENTS.NODE_CONNECT, {
      source_type: sourceType,
      target_type: targetType,
    })
  },

  nodeDisconnect: (sourceType, targetType) => {
    telemetry.track(BUILDER_EVENTS.NODE_DISCONNECT, {
      source_type: sourceType,
      target_type: targetType,
    })
  },

  nodeConfigure: (nodeType, paramName) => {
    telemetry.track(BUILDER_EVENTS.NODE_CONFIGURE, {
      node_type: nodeType,
      param_name: paramName,
    })
  },

  testRun: (templateId, nodesCount) => {
    telemetry.track(BUILDER_EVENTS.TEST_RUN, {
      template_id: templateId,
      nodes_count: nodesCount,
    })
  },

  debugToggle: (enabled) => {
    telemetry.track(BUILDER_EVENTS.DEBUG_TOGGLE, { enabled })
  },

  undo: () => {
    telemetry.track(BUILDER_EVENTS.UNDO)
  },

  redo: () => {
    telemetry.track(BUILDER_EVENTS.REDO)
  },

  zoom: (zoomLevel, method, templateId = null) => {
    telemetry.track(BUILDER_EVENTS.ZOOM, {
      zoom_level: zoomLevel,
      method,
      template_id: templateId || sessionState.currentTemplateId,
    })
  },

  fitView: (nodeCount, templateId = null) => {
    telemetry.track(BUILDER_EVENTS.FIT_VIEW, {
      node_count: nodeCount,
      template_id: templateId || sessionState.currentTemplateId,
    })
  },

  edgeCreate: (sourceType, targetType, templateId = null) => {
    telemetry.track(BUILDER_EVENTS.NODE_CONNECT, {
      source_type: sourceType,
      target_type: targetType,
      template_id: templateId || sessionState.currentTemplateId,
    })
  },
}

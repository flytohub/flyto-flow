/**
 * AI Assistant Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks AI assistant events only.
 */

import { telemetry } from '@/services/telemetry'
import { AI_EVENTS } from '@/constants/telemetryEvents'

export const trackAI = {
  chatOpen: (context = 'builder') => {
    telemetry.track(AI_EVENTS.CHAT_OPEN, { context })
  },

  chatClose: (messageCount = 0) => {
    telemetry.track(AI_EVENTS.CHAT_CLOSE, { message_count: messageCount })
  },

  messageSend: (messageLength, hasContext = false) => {
    telemetry.track(AI_EVENTS.MESSAGE_SEND, {
      message_length: messageLength,
      has_context: hasContext,
    })
  },

  messageReceive: (responseLength, responseTimeMs) => {
    telemetry.track(AI_EVENTS.MESSAGE_RECEIVE, {
      response_length: responseLength,
      response_time_ms: responseTimeMs,
    })
  },

  suggestionShow: (suggestionType, suggestionId = null) => {
    telemetry.track(AI_EVENTS.SUGGESTION_SHOW, {
      suggestion_type: suggestionType,
      suggestion_id: suggestionId,
    })
  },

  suggestionAccept: (suggestionType, suggestionId = null) => {
    telemetry.track(AI_EVENTS.SUGGESTION_ACCEPT, {
      suggestion_type: suggestionType,
      suggestion_id: suggestionId,
    })
  },

  suggestionReject: (suggestionType, suggestionId = null, reason = null) => {
    telemetry.track(AI_EVENTS.SUGGESTION_REJECT, {
      suggestion_type: suggestionType,
      suggestion_id: suggestionId,
      reason,
    })
  },

  workflowGenerateStart: (prompt) => {
    telemetry.track(AI_EVENTS.WORKFLOW_GENERATE_START, {
      prompt_length: prompt?.length || 0,
    })
  },

  workflowGenerateComplete: (nodesCount, generationTimeMs) => {
    telemetry.track(AI_EVENTS.WORKFLOW_GENERATE_COMPLETE, {
      nodes_count: nodesCount,
      generation_time_ms: generationTimeMs,
    })
  },

  workflowGenerateError: (error) => {
    telemetry.track(AI_EVENTS.WORKFLOW_GENERATE_ERROR, {
      error: typeof error === 'string' ? error : error?.message,
    })
  },

  workflowApply: (nodesCount) => {
    telemetry.track(AI_EVENTS.WORKFLOW_APPLY, { nodes_count: nodesCount })
  },

  feedbackPositive: (context) => {
    telemetry.track(AI_EVENTS.FEEDBACK_POSITIVE, { context })
  },

  feedbackNegative: (context, reason = null) => {
    telemetry.track(AI_EVENTS.FEEDBACK_NEGATIVE, { context, reason })
  },
}

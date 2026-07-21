/**
 * AI Assistant API - BYOK (Bring Your Own Key)
 *
 * All AI calls go to the local backend, which uses the user's configured
 * API key to call OpenAI/Anthropic directly.
 */

import { get, post, del } from '@/api/client'
import { ENDPOINTS } from '@/api/config'

export const aiAPI = {
  /**
   * Send a chat message to AI assistant
   * The backend handles provider selection and function calling.
   *
   * @param {Object} params - Chat parameters
   * @param {string} params.message - User message
   * @param {string} [params.sessionId] - Session ID for conversation context
   * @param {Object} [params.templateContext] - Current template state
   * @param {Array} [params.history] - Conversation history
   * @returns {Promise<Object>} { ok, message, sessionId, toolCalls, provider, model }
   */
  async sendChatMessage({
    message,
    sessionId = null,
    templateContext = null,
    history = null
  }) {
    try {
      const result = await post(ENDPOINTS.AI.CHAT, {
        message,
        sessionId,
        templateContext,
        history
      })
      return result
    } catch (err) {
      return { ok: false, error: err.message }
    }
  },

  /**
   * Get workflow suggestions
   * @param {Object} params
   * @param {string} params.query - Search query
   * @param {number} [params.limit] - Max suggestions
   * @returns {Promise<Object>}
   */
  async getSuggestions({ query, limit = 5 }) {
    try {
      return await get(ENDPOINTS.AI.SUGGESTIONS, {
        params: { context: query, limit }
      })
    } catch (err) {
      return { ok: false, suggestions: [], error: err.message }
    }
  },

  /**
   * Check AI service health
   * @returns {Promise<Object>} { ok, providers, primary, configured, model }
   */
  async checkAIHealth() {
    try {
      return await get(ENDPOINTS.AI.HEALTH)
    } catch (err) {
      return { ok: false, error: 'AI service unavailable' }
    }
  },

  /**
   * Clear a chat session
   * @param {string} sessionId
   */
  async clearSession(sessionId) {
    try {
      return await del(`/ai/session/${sessionId}`)
    } catch (err) {
      return { ok: false, error: err.message }
    }
  }
}

// Named exports for backward compatibility
export const sendChatMessage = aiAPI.sendChatMessage.bind(aiAPI)
export const getSuggestions = aiAPI.getSuggestions.bind(aiAPI)
export const checkAIHealth = aiAPI.checkAIHealth.bind(aiAPI)

export default aiAPI

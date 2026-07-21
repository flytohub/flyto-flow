/**
 * Collaboration Store — Chat Actions
 *
 * Chat message send / receive / history loading.
 */
import { get, post } from '@/api/client'

/**
 * Create chat action functions.
 * @param {Object} state - All state refs from useCollaborationState()
 * @param {Object} deps - { sendMessage } injected by index
 */
export function useChatActions(state, deps) {
  const { workflowId, chatMessages, chatLoaded } = state

  /**
   * Load chat history from REST API
   */
  async function loadChatHistory() {
    if (!workflowId.value || chatLoaded.value) return

    try {
      const convId = `collab_${workflowId.value}`
      const messages = await get(`/chat/messages?conversation_id=${convId}&limit=100`)
      if (messages && !messages.error) {
        // API returns newest first, reverse for chronological order
        chatMessages.value = (Array.isArray(messages) ? messages : []).reverse().map(msg => ({
          id: msg.id,
          senderId: msg.sender_id,
          senderName: msg.sender_name || msg.sender_id,
          senderAvatar: msg.sender_avatar || null,
          content: msg.content,
          createdAt: msg.created_at,
        }))
        chatLoaded.value = true
        // Mark messages as read
        post(`/chat/conversations/${convId}/read`).catch(() => {})
      }
    } catch (e) {
      // Silent fail — chat history load is non-critical
    }
  }

  /**
   * Send a chat message via WebSocket
   * @param {string} content - Message text
   */
  function sendChatMessage(content) {
    if (!content || !content.trim()) return
    deps.sendMessage({
      type: 'chat.message',
      content: content.trim(),
    })
  }

  return {
    loadChatHistory,
    sendChatMessage,
  }
}

/**
 * AI Chat composable — core chat message logic
 * Manages chat state, message sending, pending input forms, and session lifecycle.
 */
import { ref, computed, nextTick, watch } from 'vue'
import { sendChatMessage, aiAPI } from '@/api/ai'
import { trackAI } from '@/utils/telemetryTracker'

export function useAIChat({ t, aiSettings }) {
  const chatInput = ref('')
  const messages = ref([])
  const isTyping = ref(false)
  const pendingFormData = ref({})
  const showPasswords = ref({})
  const chatMessagesRef = ref(null)
  const inputRef = ref(null)
  const sessionId = ref(null)
  const aiProvider = ref(null)
  const aiModel = ref(null)
  const aiConfigured = ref(false)

  // Track response time
  let responseStartTime = null

  // Provider display label
  const aiProviderLabel = computed(() => {
    if (aiSettings.isConfigured) {
      return aiSettings.modelLabel
    }
    const labels = {
      openai: 'OpenAI',
      anthropic: 'Anthropic',
    }
    return labels[aiProvider.value] || aiProvider.value || ''
  })

  // Welcome message
  const welcomeMessage = computed(() => {
    return t('templateBuilder.aiChat.welcomeMessageGeneral', 'Hi! I\'m Flyto2 AI Assistant. I can help you with coding, debugging, automation, and technical questions. How can I help you today?')
  })

  async function checkAIHealth() {
    await aiSettings.loadConfig()
    try {
      const health = await aiAPI.checkAIHealth()
      aiConfigured.value = health.ok
      aiProvider.value = health.primary || null
      aiModel.value = health.model || null
    } catch (e) {
      aiConfigured.value = false
    }
  }

  async function scrollToBottom() {
    await nextTick()
    requestAnimationFrame(() => {
      if (chatMessagesRef.value) {
        chatMessagesRef.value.scrollTo({
          top: chatMessagesRef.value.scrollHeight,
          behavior: 'smooth'
        })
      }
    })
  }

  function handleEnterKey(event) {
    if (event.isComposing) return
    if (!event.shiftKey) {
      event.preventDefault()
      sendMessage()
    }
  }

  async function sendMessage() {
    const message = chatInput.value.trim()
    if (!message || !aiConfigured.value) return

    trackAI.messageSend(message.length, false)

    messages.value.push({ role: 'user', content: message })
    chatInput.value = ''

    await scrollToBottom()

    isTyping.value = true
    responseStartTime = Date.now()

    try {
      const history = messages.value
        .filter(m => m.role === 'user' || m.role === 'assistant')
        .slice(-10)
        .map(m => ({
          role: m.role === 'bot' ? 'assistant' : m.role,
          content: m.content
        }))

      const response = await sendChatMessage({
        message,
        sessionId: sessionId.value,
        history
      })

      const responseTimeMs = Date.now() - responseStartTime
      isTyping.value = false

      if (response.ok) {
        trackAI.messageReceive(response.message?.length || 0, responseTimeMs)

        if (response.sessionId) {
          sessionId.value = response.sessionId
        }

        // Update provider info from response
        if (response.provider) {
          aiProvider.value = response.provider
        }
        if (response.model) {
          aiModel.value = response.model
        }

        const botMsg = {
          role: 'bot',
          content: response.message,
          pendingInput: response.pending_input || response.pendingInput || null,
          inputAnswered: false,
        }
        messages.value.push(botMsg)

        // Initialize form data with defaults/prefills
        if (botMsg.pendingInput) {
          const formInit = {}
          for (const field of botMsg.pendingInput.fields || []) {
            formInit[field.id] = field.prefill || field.default || (field.type === 'confirm' ? false : '')
          }
          pendingFormData.value = formInit
          showPasswords.value = {}
        }
      } else {
        messages.value.push({
          role: 'bot',
          content: response.message || t('templateBuilder.aiChat.errorGeneric'),
          pendingInput: null,
          inputAnswered: false,
        })
      }
    } catch (error) {
      isTyping.value = false
      messages.value.push({
        role: 'bot',
        content: t('templateBuilder.aiChat.errorConnection')
      })
    }

    await scrollToBottom()
  }

  async function submitPendingInput(msgIndex) {
    const msg = messages.value[msgIndex]
    if (!msg?.pendingInput) return

    // Mark as answered so form hides
    msg.inputAnswered = true

    // Build response text (mask passwords)
    const parts = []
    for (const field of msg.pendingInput.fields) {
      const val = pendingFormData.value[field.id]
      if (val !== undefined && val !== '' && val !== null) {
        if (field.type === 'password') {
          parts.push(`${field.label}: ***`)
        } else {
          parts.push(`${field.label}: ${val}`)
        }
      }
    }

    // Send as user message with actual values (unmasked for the agent)
    const responseText = Object.entries(pendingFormData.value)
      .filter(([, v]) => v !== '' && v !== null && v !== undefined)
      .map(([k, v]) => `${k}: ${v}`)
      .join(', ')

    // Show masked version in chat
    messages.value.push({
      role: 'user',
      content: parts.join('\n') || 'Submitted',
    })

    await scrollToBottom()
    isTyping.value = true
    responseStartTime = Date.now()

    try {
      const history = messages.value
        .filter(m => m.role === 'user' || m.role === 'assistant' || m.role === 'bot')
        .slice(-10)
        .map(m => ({
          role: m.role === 'bot' ? 'assistant' : m.role,
          content: m.content
        }))

      const response = await sendChatMessage({
        message: `[User provided: ${responseText}]`,
        sessionId: sessionId.value,
        history
      })

      isTyping.value = false

      if (response.ok) {
        if (response.sessionId) sessionId.value = response.sessionId

        const botMsg = {
          role: 'bot',
          content: response.message,
          pendingInput: response.pending_input || response.pendingInput || null,
          inputAnswered: false,
        }
        messages.value.push(botMsg)

        if (botMsg.pendingInput) {
          const formInit = {}
          for (const field of botMsg.pendingInput.fields || []) {
            formInit[field.id] = field.prefill || field.default || (field.type === 'confirm' ? false : '')
          }
          pendingFormData.value = formInit
          showPasswords.value = {}
        }
      } else {
        messages.value.push({ role: 'bot', content: response.message || 'Error' })
      }
    } catch (error) {
      isTyping.value = false
      messages.value.push({ role: 'bot', content: t('templateBuilder.aiChat.errorConnection') })
    }

    await scrollToBottom()
    pendingFormData.value = {}
  }

  function cancelPendingInput(msgIndex) {
    const msg = messages.value[msgIndex]
    if (msg) msg.inputAnswered = true
    pendingFormData.value = {}
  }

  function clearChat() {
    if (sessionId.value) {
      aiAPI.clearSession(sessionId.value)
    }
    messages.value = []
    sessionId.value = null
  }

  watch(messages, scrollToBottom, { deep: true })

  return {
    chatInput,
    messages,
    isTyping,
    pendingFormData,
    showPasswords,
    chatMessagesRef,
    inputRef,
    sessionId,
    aiProvider,
    aiModel,
    aiConfigured,
    aiProviderLabel,
    welcomeMessage,
    checkAIHealth,
    scrollToBottom,
    handleEnterKey,
    sendMessage,
    submitPendingInput,
    cancelPendingInput,
    clearChat,
  }
}

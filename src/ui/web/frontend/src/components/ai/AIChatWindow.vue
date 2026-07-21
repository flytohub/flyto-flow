<template>
  <Teleport to="body">
    <Transition name="chat-slide">
      <div v-if="show" class="ai-chat-window">
        <!-- Chat Header -->
        <div class="chat-header">
          <div class="chat-header-left">
            <div class="chat-avatar">
              <Bot :size="20" />
            </div>
            <div class="chat-title">
              <h4>{{ $t('templateBuilder.aiChat.botName') }}</h4>
              <span class="chat-status" v-if="aiProvider">
                <span class="status-dot"></span>
                <Sparkles :size="12" />
                {{ aiProviderLabel }}
              </span>
              <span class="chat-status not-configured" v-else>
                <span class="status-dot offline"></span>
                {{ $t('templateBuilder.aiChat.notConfigured', 'Not configured') }}
              </span>
            </div>
          </div>
          <div class="chat-header-actions">
            <button class="chat-action-btn" :title="$t('templateBuilder.aiChat.clearChat')" @click="clearChat">
              <Trash2 :size="14" />
            </button>
            <button @click="$emit('close')" class="chat-action-btn close" :title="$t('templateBuilder.aiChat.close')">
              <X :size="16" />
            </button>
          </div>
        </div>

        <!-- Chat Messages -->
        <div class="chat-messages custom-scrollbar" ref="chatMessagesRef">
          <!-- No API Key Setup Guide -->
          <div v-if="!aiConfigured" class="setup-guide">
            <div class="setup-icon">
              <KeyRound :size="32" />
            </div>
            <h3>{{ $t('templateBuilder.aiChat.setupTitle', 'Set up AI Assistant') }}</h3>
            <p>{{ $t('templateBuilder.aiChat.setupDesc', 'Configure your OpenAI or Anthropic API key to start using the AI assistant.') }}</p>
            <button @click="goToSettings" class="setup-btn" aria-label="Go to settings">
              <Settings :size="16" />
              {{ $t('templateBuilder.aiChat.goToSettings', 'Go to Settings') }}
            </button>
          </div>

          <!-- Welcome Message (when configured) -->
          <ChatMessage
            v-if="aiConfigured"
            role="bot"
            :content="welcomeMessage"
          />

          <!-- User/Bot Messages -->
          <template v-for="(msg, index) in messages" :key="index">
            <ChatMessage
              :role="msg.role === 'bot' ? 'bot' : 'user'"
              :content="msg.content"
            />
            <!-- Pending Input Form (ask_user) -->
            <div v-if="msg.pendingInput && !msg.inputAnswered" class="pending-input-card">
              <div class="pending-input-header">
                <KeyRound :size="14" />
                <span>{{ msg.pendingInput.question }}</span>
              </div>
              <div class="pending-input-fields">
                <div v-for="field in msg.pendingInput.fields" :key="field.id" class="pending-field">
                  <!-- Saved account / login method selector -->
                  <template v-if="field.id === '_saved_account' || field.id === '_login_method'">
                    <label class="field-label">{{ field.label }}</label>
                    <div class="field-chips">
                      <button
                        v-for="opt in field.options" :key="opt"
                        class="field-chip"
                        :class="{
                          active: pendingFormData[field.id] === opt,
                          'chip-apple': opt.toLowerCase().includes('apple'),
                          'chip-google': opt.toLowerCase().includes('google'),
                          'chip-add': opt.includes('+'),
                        }"
                        @click="pendingFormData[field.id] = opt"
                      >
                        <span v-if="opt.toLowerCase().includes('apple')" class="chip-icon">🍎</span>
                        <span v-else-if="opt.toLowerCase().includes('google')" class="chip-icon">🔵</span>
                        <span v-else-if="opt.includes('+')" class="chip-icon">➕</span>
                        {{ opt }}
                      </button>
                    </div>
                  </template>
                  <!-- Password field -->
                  <template v-else-if="field.type === 'password'">
                    <label class="field-label">{{ field.label }}</label>
                    <div class="field-password-wrap">
                      <input
                        :type="showPasswords[field.id] ? 'text' : 'password'"
                        v-model="pendingFormData[field.id]"
                        :placeholder="field.label"
                        class="field-input"
                      />
                      <button class="field-eye-btn" @click="showPasswords[field.id] = !showPasswords[field.id]" aria-label="Toggle password visibility">
                        <component :is="showPasswords[field.id] ? EyeOff : Eye" :size="14" />
                      </button>
                    </div>
                  </template>
                  <!-- Select field -->
                  <template v-else-if="field.type === 'select'">
                    <label class="field-label">{{ field.label }}</label>
                    <div class="field-chips">
                      <button
                        v-for="opt in field.options" :key="opt"
                        class="field-chip"
                        :class="{ active: pendingFormData[field.id] === opt }"
                        @click="pendingFormData[field.id] = opt"
                        :aria-label="opt"
                      >{{ opt }}</button>
                    </div>
                  </template>
                  <!-- Confirm (toggle) -->
                  <template v-else-if="field.type === 'confirm'">
                    <label class="field-label field-toggle-label">
                      <span>{{ field.label }}</span>
                      <button
                        class="field-toggle"
                        :class="{ on: pendingFormData[field.id] }"
                        @click="pendingFormData[field.id] = !pendingFormData[field.id]"
                        aria-label="Toggle"
                      >
                        <span class="toggle-knob"></span>
                      </button>
                    </label>
                  </template>
                  <!-- Text / number / date -->
                  <template v-else>
                    <label class="field-label">{{ field.label }}</label>
                    <input
                      :type="field.type === 'number' ? 'number' : field.type === 'date' ? 'date' : 'text'"
                      v-model="pendingFormData[field.id]"
                      :placeholder="field.label"
                      class="field-input"
                    />
                  </template>
                </div>
              </div>
              <div class="pending-input-actions">
                <button class="pending-cancel-btn" @click="cancelPendingInput(index)" aria-label="Cancel">
                  {{ $t('common.cancel', 'Cancel') }}
                </button>
                <button class="pending-submit-btn" @click="submitPendingInput(index)" aria-label="Submit">
                  <Send :size="14" />
                  {{ $t('common.submit', 'Submit') }}
                </button>
              </div>
            </div>
          </template>

          <!-- Typing Indicator -->
          <div v-if="isTyping" class="chat-message bot typing">
            <div class="message-avatar">
              <Bot :size="16" />
            </div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Chat Input -->
        <div class="chat-input-container">
          <textarea
            v-model="chatInput"
            @keydown.enter="handleEnterKey"
            :placeholder="aiConfigured
              ? $t('templateBuilder.aiChat.inputPlaceholder', 'Ask me anything...')
              : $t('templateBuilder.aiChat.configureFirst', 'Configure API key first...')"
            class="chat-input"
            rows="1"
            ref="inputRef"
            :disabled="!aiConfigured"
          ></textarea>
          <button @click="sendMessage" class="chat-send-btn" :disabled="!chatInput.trim() || isTyping || !aiConfigured" aria-label="Send message">
            <Send :size="18" />
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Bot, Trash2, X, Send, Sparkles, KeyRound, Settings, Eye, EyeOff } from 'lucide-vue-next'
import ChatMessage from './ChatMessage.vue'
import { trackAI } from '@/utils/telemetryTracker'
import { useAISettingsStore } from '@/stores/aiSettingsStore'
import { useAIChat } from '@/composables/useAIChat'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const { t } = useI18n()
const router = useRouter()
const aiSettings = useAISettingsStore()

const {
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
  handleEnterKey,
  sendMessage,
  submitPendingInput,
  cancelPendingInput,
  clearChat,
} = useAIChat({ t, aiSettings })

// Check AI availability on mount
onMounted(() => checkAIHealth())

// Track chat open/close
watch(() => props.show, (newVal, oldVal) => {
  if (newVal && !oldVal) {
    trackAI.chatOpen('builder')
  } else if (!newVal && oldVal) {
    trackAI.chatClose(messages.value.length)
  }
})

function goToSettings() {
  emit('close')
  router.push('/settings')
}
</script>

<style scoped>
/* AI Chat Floating Window */
.ai-chat-window {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 420px;
  height: 600px;
  max-height: calc(100vh - 120px);
  background: linear-gradient(180deg, #0c1222 0%, #070b14 100%);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 1000;
  box-shadow:
    0 25px 80px rgba(0, 0, 0, 0.6),
    0 0 60px rgba(16, 185, 129, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

/* Chat Header */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(6, 182, 212, 0.05) 100%);
  border-bottom: 1px solid rgba(71, 85, 105, 0.4);
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-avatar {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: linear-gradient(135deg, #10B981 0%, #06B6D4 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
}

.chat-title h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #f1f5f9;
}

.chat-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #10B981;
}

.chat-status.not-configured {
  color: #F59E0B;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10B981;
  box-shadow: 0 0 8px #10B981;
  animation: pulse-dot 2s ease-in-out infinite;
}

.status-dot.offline {
  background: #F59E0B;
  box-shadow: 0 0 8px #F59E0B;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.8); }
}

.chat-header-actions {
  display: flex;
  gap: 8px;
}

.chat-action-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.4);
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.chat-action-btn:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #e2e8f0;
}

.chat-action-btn.close:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.4);
  color: #f87171;
}

/* Chat Messages */
.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-message {
  display: flex;
  gap: 12px;
  max-width: 90%;
}

.chat-message.user {
  flex-direction: row-reverse;
  align-self: flex-end;
}

.chat-message.bot {
  align-self: flex-start;
}

.message-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-message.bot .message-avatar {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(6, 182, 212, 0.15) 100%);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #34d399;
}

.chat-message.user .message-avatar {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(99, 102, 241, 0.15) 100%);
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: #a78bfa;
}

.message-content {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 13px;
  line-height: 1.5;
}

.chat-message.bot .message-content {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
  border: 1px solid rgba(71, 85, 105, 0.4);
  color: #e2e8f0;
  border-top-left-radius: 4px;
}

.chat-message.user .message-content {
  background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
  color: white;
  border-top-right-radius: 4px;
}

/* Setup Guide (no API key) */
.setup-guide {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 32px 24px;
  gap: 12px;
}

.setup-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(6, 182, 212, 0.1) 100%);
  border: 1px solid rgba(16, 185, 129, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #10B981;
  margin-bottom: 8px;
}

.setup-guide h3 {
  font-size: 16px;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0;
}

.setup-guide p {
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.5;
  max-width: 300px;
}

.setup-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #10B981 0%, #06B6D4 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 8px;
}

.setup-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.3);
}

/* Typing Indicator */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #64748b;
  animation: typing-bounce 1.4s ease-in-out infinite;
}

.typing-indicator span:nth-child(1) { animation-delay: 0s; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing-bounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-8px); opacity: 1; }
}

/* Chat Input */
.chat-input-container {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(7, 11, 20, 0.9) 100%);
  border-top: 1px solid rgba(71, 85, 105, 0.4);
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 12px;
  color: #e2e8f0;
  font-size: 13px;
  resize: none;
  max-height: 120px;
  transition: all 0.2s;
}

.chat-input:focus {
  outline: none;
  border-color: #10B981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
}

.chat-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-input::placeholder {
  color: #64748b;
}

.chat-send-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #10B981 0%, #06B6D4 100%);
  border: none;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
}

.chat-send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 6px 25px rgba(16, 185, 129, 0.4);
}

.chat-send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
}

/* Custom Scrollbar */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}

/* Pending Input Form (ask_user) */
.pending-input-card {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.06) 0%, rgba(6, 182, 212, 0.04) 100%);
  border: 1px solid rgba(16, 185, 129, 0.25);
  border-radius: 16px;
  padding: 16px;
  max-width: 95%;
  align-self: flex-start;
  animation: fade-in-up 0.3s ease;
}

@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.pending-input-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #10B981;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 14px;
}

.pending-input-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pending-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-label {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.field-input {
  padding: 10px 12px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 10px;
  color: #e2e8f0;
  font-size: 13px;
  transition: all 0.2s;
}

.field-input:focus {
  outline: none;
  border-color: #10B981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
}

.field-password-wrap {
  position: relative;
}

.field-password-wrap .field-input {
  width: 100%;
  padding-right: 36px;
}

.field-eye-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 4px;
  display: flex;
}

.field-eye-btn:hover { color: #94a3b8; }

.field-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.field-chip {
  padding: 6px 12px;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 20px;
  color: #94a3b8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.field-chip:hover {
  border-color: rgba(16, 185, 129, 0.4);
  color: #e2e8f0;
}

.field-chip.active {
  background: rgba(16, 185, 129, 0.15);
  border-color: #10B981;
  color: #10B981;
}

.field-toggle-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.field-toggle {
  width: 40px;
  height: 22px;
  border-radius: 11px;
  background: rgba(71, 85, 105, 0.5);
  border: none;
  cursor: pointer;
  position: relative;
  transition: background 0.2s;
}

.field-toggle.on {
  background: #10B981;
}

.toggle-knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: white;
  transition: transform 0.2s;
}

.field-toggle.on .toggle-knob {
  transform: translateX(18px);
}

.pending-input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 14px;
}

.pending-cancel-btn {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 10px;
  color: #94a3b8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.pending-cancel-btn:hover {
  border-color: rgba(239, 68, 68, 0.4);
  color: #f87171;
}

.pending-submit-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #10B981 0%, #06B6D4 100%);
  border: none;
  border-radius: 10px;
  color: white;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.pending-submit-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
}

/* Chat Window Transition */
.chat-slide-enter-active,
.chat-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.chat-slide-enter-from,
.chat-slide-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}
</style>

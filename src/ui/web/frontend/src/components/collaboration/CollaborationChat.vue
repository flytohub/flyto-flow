<template>
  <div class="chat-section">
    <div class="chat-messages" ref="chatContainer">
      <div v-if="chatMessages.length === 0" class="chat-empty">
        <MessageSquare :size="20" />
        <span>{{ $t('collaboration.chat.empty', 'No messages yet') }}</span>
      </div>
      <div v-for="msg in chatMessages" :key="msg.id" class="chat-msg" :class="{ 'is-own': msg.senderId === currentUserId }">
        <div class="chat-avatar-small" v-if="msg.senderId !== currentUserId">
          <img v-if="msg.senderAvatar" :src="msg.senderAvatar" :alt="msg.senderName" />
          <span v-else>{{ getInitials(msg.senderName) }}</span>
        </div>
        <div class="chat-bubble">
          <span class="chat-sender" v-if="msg.senderId !== currentUserId">{{ msg.senderName }}</span>
          <span class="chat-text">{{ msg.content }}</span>
          <span class="chat-time">{{ formatChatTime(msg.createdAt) }}</span>
        </div>
      </div>
    </div>
    <div class="chat-input-row">
      <AppInput
        v-model="chatInput"
        @keyup.enter="handleSendChat"
        :placeholder="$t('collaboration.chat.placeholder', 'Message...')"
        class="chat-input"
        maxlength="2000"
      />
      <button class="chat-send-btn" @click="handleSendChat" :disabled="!chatInput.trim()" aria-label="Send message">
        <Send :size="14" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { MessageSquare, Send } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'

const props = defineProps({
  chatMessages: { type: Array, default: () => [] },
  currentUserId: { type: String, default: null },
})

const emit = defineEmits(['send-chat'])

const chatInput = ref('')
const chatContainer = ref(null)

function handleSendChat() {
  const content = chatInput.value.trim()
  if (!content) return
  emit('send-chat', content)
  chatInput.value = ''
}

function getInitials(name) {
  if (!name) return '?'
  const parts = name.split(' ')
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name.substring(0, 2).toUpperCase()
}

function formatChatTime(isoStr) {
  if (!isoStr) return ''
  try {
    const date = new Date(isoStr)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

// Auto-scroll chat to bottom when new messages arrive
watch(() => props.chatMessages.length, async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
})
</script>

<style scoped>
/* Chat Section — fills all remaining space */
.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-top: 1px solid rgba(148, 163, 184, 0.1);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  min-height: 0;
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 100%;
  min-height: 80px;
  font-size: 12px;
  color: #475569;
}

.chat-msg {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  margin-bottom: 8px;
}

.chat-msg:last-child { margin-bottom: 0; }

.chat-msg.is-own {
  flex-direction: row-reverse;
}

.chat-msg.is-own .chat-bubble {
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.18) 0%, rgba(139, 92, 246, 0.18) 100%);
  border-color: rgba(6, 182, 212, 0.25);
}

.chat-avatar-small {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: linear-gradient(135deg, #475569 0%, #334155 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 8px;
  font-weight: 700;
  color: #e2e8f0;
}

.chat-avatar-small img { width: 100%; height: 100%; object-fit: cover; }

.chat-bubble {
  max-width: 80%;
  padding: 6px 10px;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.08);
  border-radius: 10px;
}

.chat-sender {
  display: block;
  font-size: 10px;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 2px;
}

.chat-text {
  font-size: 13px;
  color: #e2e8f0;
  line-height: 1.4;
  word-break: break-word;
}

.chat-time {
  display: block;
  font-size: 9px;
  color: #475569;
  margin-top: 2px;
  text-align: right;
}

.chat-input-row {
  display: flex;
  gap: 6px;
  padding: 8px 12px;
  border-top: 1px solid rgba(148, 163, 184, 0.1);
  flex-shrink: 0;
}

.chat-input {
  flex: 1;
  padding: 8px 12px;
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 8px;
  font-size: 13px;
  color: #e2e8f0;
  outline: none;
}

.chat-input::placeholder { color: #475569; }
.chat-input:focus { border-color: rgba(6, 182, 212, 0.4); }

.chat-send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, #06b6d4 0%, #8b5cf6 100%);
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.chat-send-btn:hover:not(:disabled) { transform: scale(1.05); }
.chat-send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.chat-messages::-webkit-scrollbar { width: 4px; }
.chat-messages::-webkit-scrollbar-track { background: transparent; }
.chat-messages::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.2); border-radius: 2px; }
</style>

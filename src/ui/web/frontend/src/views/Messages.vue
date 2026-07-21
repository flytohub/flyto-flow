<template>
  <div class="h-[calc(100vh-5rem)] bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 relative overflow-hidden">
    <!-- Background -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl"></div>
      <div class="absolute top-1/2 -left-40 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl"></div>
    </div>

    <!-- Content -->
    <main class="relative h-full p-4">
      <div class="flex gap-4 h-full">
        <!-- Conversation List -->
        <div class="w-80 flex-shrink-0 bg-gray-800/50 backdrop-blur-xl rounded-xl border border-white/10 overflow-hidden flex flex-col">
          <!-- Search -->
          <div class="p-4 border-b border-white/10">
            <div class="relative">
              <Search :size="18" class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
              <AppInput
                v-model="searchQuery"
                :placeholder="t('chat.searchConversations')"
                class="!pl-10"
              />
            </div>
          </div>

          <!-- Conversations -->
          <div class="flex-1 overflow-y-auto">
            <div v-if="loading" class="flex justify-center items-center h-32">
              <Loader2 :size="24" class="animate-spin text-purple-500" />
            </div>
            <div v-else-if="filteredConversations.length === 0" class="flex flex-col items-center justify-center h-32 text-gray-500">
              <MessageSquare :size="32" class="mb-2 opacity-50" />
              <p class="text-sm">{{ t('chat.noConversations') }}</p>
            </div>
            <div v-else class="divide-y divide-white/5">
              <div
                v-for="conv in filteredConversations"
                :key="conv.id"
                @click="selectConversation(conv)"
                :class="[
                  'flex items-center gap-3 p-4 cursor-pointer transition-all',
                  selected?.id === conv.id ? 'bg-purple-500/20 border-l-2 border-purple-500' : 'hover:bg-white/5'
                ]"
              >
                <div class="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-semibold">
                  {{ (conv.otherUser?.displayName || 'U').charAt(0).toUpperCase() }}
                </div>
                <div class="flex-1 min-w-0">
                  <span class="font-medium text-white truncate block">{{ conv.otherUser?.displayName || t('chat.user') }}</span>
                  <p class="text-sm text-gray-400 truncate">{{ conv.lastMessage || t('chat.noMessages') }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Chat Area -->
        <div class="flex-1 bg-gray-800/50 backdrop-blur-xl rounded-xl border border-white/10 overflow-hidden flex flex-col">
          <!-- No Selection -->
          <div v-if="!selected" class="flex-1 flex flex-col items-center justify-center text-gray-500">
            <MessageSquare :size="40" class="text-purple-400 mb-4" />
            <p class="text-lg font-medium text-white">{{ t('chat.selectConversation') }}</p>
          </div>

          <!-- Chat -->
          <template v-else>
            <!-- Header -->
            <div class="flex items-center gap-3 p-4 border-b border-white/10">
              <div class="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-semibold">
                {{ (selected.otherUser?.displayName || 'U').charAt(0).toUpperCase() }}
              </div>
              <h3 class="font-semibold text-white">{{ selected.otherUser?.displayName || t('chat.user') }}</h3>
            </div>

            <!-- Messages -->
            <div class="flex-1 overflow-y-auto p-4 space-y-2" ref="messagesRef">
              <div v-if="loadingMessages" class="flex justify-center py-8">
                <Loader2 :size="24" class="animate-spin text-purple-500" />
              </div>
              <div
                v-for="msg in messages"
                :key="msg.id"
                :class="[
                  'max-w-[70%] p-3 rounded-xl',
                  msg.senderId === currentUserId
                    ? 'ml-auto bg-purple-600 text-white'
                    : 'bg-gray-700 text-white'
                ]"
              >
                {{ msg.content }}
              </div>
            </div>

            <!-- Input -->
            <div class="p-4 border-t border-white/10">
              <div class="flex gap-3">
                <AppInput
                  v-model="inputText"
                  @keydown="e => { if (e.key === 'Enter') sendMessage() }"
                  :placeholder="t('chat.typePlaceholder')"
                />
                <button
                  @click="sendMessage"
                  :disabled="!inputText.trim()"
                  class="p-3 bg-purple-600 text-white rounded-xl disabled:opacity-50"
                  aria-label="Send"
                >
                  <Send :size="20" />
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { MessageSquare, Search, Loader2, Send } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import { get, post } from '@/api/client'
import { ENDPOINTS } from '@/api/config'
import { authAPI } from '@/api/auth'

const { t } = useI18n()

// State
const conversations = ref([])
const messages = ref([])
const selected = ref(null)
const loading = ref(false)
const loadingMessages = ref(false)
const inputText = ref('')
const searchQuery = ref('')
const messagesRef = ref(null)
const currentUserId = ref('')

// Filtered list
const filteredConversations = computed(() => {
  if (!searchQuery.value.trim()) return conversations.value
  const q = searchQuery.value.toLowerCase()
  return conversations.value.filter(c => c.otherUser?.displayName?.toLowerCase().includes(q))
})

// Load conversations
async function loadConversations() {
  loading.value = true
  try {
    const result = await get(ENDPOINTS.CHAT.CONVERSATIONS, { params: { page: 1, pageSize: 100 } })
    conversations.value = result.items || []
  } catch (e) {
    conversations.value = []
  } finally {
    loading.value = false
  }
}

// Load messages
async function loadMessages(conversationId) {
  loadingMessages.value = true
  try {
    const result = await get(ENDPOINTS.CHAT.MESSAGES, { params: { conversationId, limit: 100 } })
    messages.value = Array.isArray(result) ? result : (result.items || [])
  } catch (e) {
    messages.value = []
  } finally {
    loadingMessages.value = false
  }
}

// Select conversation
async function selectConversation(conv) {
  selected.value = conv
  await loadMessages(conv.id)
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

// Send message
async function sendMessage() {
  if (!inputText.value.trim() || !selected.value) return

  const text = inputText.value.trim()
  inputText.value = ''

  try {
    const result = await post(ENDPOINTS.CHAT.MESSAGES, {
      conversationId: selected.value.id,
      content: text,
      messageType: 'text'
    })

    if (result?.id) {
      messages.value.push({
        id: result.id,
        senderId: currentUserId.value,
        content: text,
        createdAt: new Date().toISOString()
      })
      await nextTick()
      if (messagesRef.value) {
        messagesRef.value.scrollTop = messagesRef.value.scrollHeight
      }
    }
  } catch (e) {
    inputText.value = text
  }
}

// Init
onMounted(async () => {
  const user = authAPI.getLocalUser()
  currentUserId.value = user?.id || user?.uid || ''
  await loadConversations()
})
</script>

<template>
  <Transition name="slide">
    <div v-if="isOpen" class="collaboration-panel">
      <!-- Header -->
      <div class="panel-header">
        <div class="header-title">
          <div class="header-icon">
            <Users :size="18" />
          </div>
          <span>{{ $t('collaboration.title', 'Collaborators') }}</span>
          <span class="participant-count">{{ participants.length }}</span>
        </div>
        <button class="close-btn" @click="$emit('close')" aria-label="Close">
          <X :size="16" />
        </button>
      </div>

      <!-- Session info -->
      <div class="session-info">
        <!-- Error state -->
        <div v-if="connectionError" class="collab-error-banner">
          <AlertCircle :size="14" />
          <span>{{ connectionError }}</span>
        </div>
        <!-- Connecting state -->
        <div v-else-if="isConnecting" class="connecting-indicator">
          <div class="connecting-spinner"></div>
          <span>{{ $t('collaboration.connecting', 'Connecting...') }}</span>
        </div>
        <!-- Not connected, no error -->
        <div v-else-if="!isLive && !isConnecting" class="not-connected-indicator">
          <WifiOff :size="14" />
          <span>{{ $t('collaboration.notConnected', 'Not connected') }}</span>
        </div>
        <!-- Connected -->
        <div class="live-indicator" v-if="isLive">
          <div class="live-pulse"></div>
          <span>{{ $t('collaboration.realtime', 'Real-time sync active') }}</span>
        </div>
        <div v-if="!quotaInfo.isUnlimited && quotaInfo.remainingMinutes !== null" class="quota-info">
          <Clock :size="12" />
          <span>{{ formatRemainingTime(quotaInfo.remainingMinutes) }} {{ $t('collaboration.remaining', 'remaining') }}</span>
        </div>
      </div>

      <!-- Participants list -->
      <CollaboratorList
        :participants="participants"
        :current-user-id="currentUserId"
      />

      <!-- Chat -->
      <CollaborationChat
        :chat-messages="chatMessages"
        :current-user-id="currentUserId"
        @send-chat="$emit('send-chat', $event)"
      />

      <!-- Actions (fixed bottom) -->
      <div class="panel-actions">
        <button class="action-btn invite" @click="$emit('invite')" aria-label="Invite">
          <UserPlus :size="14" />
          <span>{{ $t('collaboration.invite', 'Invite') }}</span>
        </button>
        <button v-if="isOwner" class="action-btn terminate" @click="confirmTerminate" aria-label="End session">
          <XCircle :size="14" />
          <span>{{ $t('collaboration.endSession', 'End Session') }}</span>
        </button>
      </div>

      <!-- Terminate confirmation overlay -->
      <Transition name="fade">
        <div v-if="showTerminateConfirm" class="terminate-confirm">
          <p>{{ $t('collaboration.endSessionConfirm', 'End collaboration for all participants?') }}</p>
          <div class="terminate-actions">
            <button class="btn-cancel-sm" @click="showTerminateConfirm = false" aria-label="Cancel">
              {{ $t('common.cancel', 'Cancel') }}
            </button>
            <button class="btn-terminate" @click="handleTerminate" aria-label="End now">
              {{ $t('collaboration.endNow', 'End Now') }}
            </button>
          </div>
        </div>
      </Transition>
    </div>
  </Transition>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Users, X, UserPlus, Clock, XCircle, AlertCircle, WifiOff } from 'lucide-vue-next'
import CollaboratorList from '@/components/collaboration/CollaboratorList.vue'
import CollaborationChat from '@/components/collaboration/CollaborationChat.vue'

const { t } = useI18n()

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  sessionId: { type: String, default: '' },
  participants: { type: Array, default: () => [] },
  currentUserId: { type: String, default: null },
  isLive: { type: Boolean, default: false },
  isConnecting: { type: Boolean, default: false },
  connectionError: { type: String, default: null },
  isOwner: { type: Boolean, default: false },
  quotaInfo: { type: Object, default: () => ({ isUnlimited: true, remainingMinutes: null }) },
  chatMessages: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'invite', 'send-chat', 'terminate'])

// Terminate
const showTerminateConfirm = ref(false)
function confirmTerminate() { showTerminateConfirm.value = true }
function handleTerminate() {
  showTerminateConfirm.value = false
  emit('terminate')
}

function formatRemainingTime(minutes) {
  if (minutes === null || minutes === undefined) return ''
  if (minutes >= 60) {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    if (mins === 0) return `${hours}h`
    return `${hours}h ${mins}m`
  }
  return `${minutes}m`
}
</script>

<style scoped>
.collaboration-panel {
  position: fixed;
  top: 64px;
  right: 0;
  width: 320px;
  height: calc(100vh - 64px);
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%);
  backdrop-filter: blur(20px);
  border-left: 1px solid rgba(148, 163, 184, 0.1);
  display: flex;
  flex-direction: column;
  z-index: 1000;
  box-shadow: -12px 0 40px rgba(0, 0, 0, 0.4);
}

/* Header */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
  flex-shrink: 0;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 600;
  color: #f1f5f9;
}

.header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%);
  border-radius: 8px;
  color: #06b6d4;
}

.participant-count {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 11px;
  font-size: 11px;
  font-weight: 700;
  color: #06b6d4;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  background: rgba(71, 85, 105, 0.2);
  border: 1px solid rgba(148, 163, 184, 0.1);
  border-radius: 8px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #f87171;
}

/* Session info */
.session-info {
  padding: 10px 16px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
  flex-shrink: 0;
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #22c55e;
}

.live-pulse {
  position: relative;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
}

.live-pulse::before {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  background: rgba(34, 197, 94, 0.4);
  animation: pulse-ring 1.5s ease-out infinite;
}

@keyframes pulse-ring {
  0% { transform: scale(0.8); opacity: 1; }
  100% { transform: scale(1.8); opacity: 0; }
}

.collab-error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #f87171;
  padding: 8px 10px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 6px;
}

.connecting-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #94a3b8;
}

.connecting-spinner {
  width: 10px;
  height: 10px;
  border: 2px solid rgba(148, 163, 184, 0.3);
  border-top-color: #94a3b8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.not-connected-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #64748b;
}

.quota-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #fbbf24;
  margin-top: 8px;
  padding: 6px 10px;
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.2);
  border-radius: 6px;
}

/* Actions (fixed bottom) */
.panel-actions {
  padding: 10px 12px;
  border-top: 1px solid rgba(148, 163, 184, 0.1);
  flex-shrink: 0;
}

.action-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.invite {
  background: linear-gradient(135deg, #06b6d4 0%, #8b5cf6 100%);
  border: none;
  color: white;
  box-shadow: 0 4px 15px rgba(6, 182, 212, 0.25);
}

.action-btn.invite:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(6, 182, 212, 0.35);
}

.action-btn.terminate {
  background: transparent;
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
  margin-top: 6px;
}

.action-btn.terminate:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.5);
}

/* Terminate confirmation */
.terminate-confirm {
  position: absolute;
  bottom: 60px;
  left: 12px;
  right: 12px;
  padding: 14px;
  background: rgba(15, 23, 42, 0.98);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  z-index: 10;
}

.terminate-confirm p {
  font-size: 13px;
  color: #f1f5f9;
  margin: 0 0 12px;
}

.terminate-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.btn-cancel-sm {
  padding: 6px 14px;
  background: transparent;
  border: 1px solid #475569;
  border-radius: 6px;
  font-size: 12px;
  color: #94a3b8;
  cursor: pointer;
}

.btn-cancel-sm:hover {
  background: rgba(71, 85, 105, 0.3);
}

.btn-terminate {
  padding: 6px 14px;
  background: rgba(239, 68, 68, 0.8);
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: white;
  cursor: pointer;
}

.btn-terminate:hover {
  background: rgba(239, 68, 68, 1);
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.15s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* Slide Transition */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>

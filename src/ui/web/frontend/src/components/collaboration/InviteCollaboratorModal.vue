<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
        <div class="modal-container">
          <!-- Header -->
          <div class="modal-header">
            <div class="header-icon">
              <UserPlus :size="24" />
            </div>
            <div class="header-text">
              <h2>{{ $t('collaboration.invite.title', 'Invite Collaborators') }}</h2>
              <p>{{ $t('collaboration.invite.subtitle', 'Share the invite code for real-time collaboration') }}</p>
            </div>
            <button class="close-btn" @click="$emit('close')" aria-label="Close">
              <X :size="20" />
            </button>
          </div>

          <!-- Content -->
          <div class="modal-content">
            <!-- Invite Code Section (owner only) -->
            <div class="invite-code-section" v-if="inviteCode || isLoadingCode">
              <label class="section-label">
                <Key :size="16" />
                {{ $t('collaboration.invite.inviteCode', 'Invite Code') }}
              </label>
              <div class="code-display">
                <div class="code-value" @click="copyCode" :class="{ loading: isLoadingCode }">
                  <Loader v-if="isLoadingCode" :size="20" class="spin" />
                  <template v-else>{{ inviteCode }}</template>
                </div>
                <button class="copy-btn" @click="copyCode" :disabled="isLoadingCode" aria-label="Copy code">
                  <Check v-if="copied" :size="16" />
                  <Copy v-else :size="16" />
                </button>
              </div>
              <p class="helper-text">
                {{ $t('collaboration.invite.codeHelp', 'Share this code with your team. They must request to join, then you approve.') }}
              </p>
            </div>

            <!-- Join Section -->
            <div class="join-section">
              <label class="section-label">
                <LogIn :size="16" />
                {{ $t('collaboration.invite.joinSession', 'Join a Session') }}
              </label>

              <!-- Step 1: Enter code -->
              <div v-if="!joinConfirm" class="join-input-group">
                <AppInput
                  v-model="joinCode"
                  :placeholder="$t('collaboration.invite.enterCode', 'Enter invite code...')"
                  class="join-input"
                  @keyup.enter="handleResolveCode"
                />
                <button class="join-btn" @click="handleResolveCode" :disabled="!joinCode.trim() || isJoining">
                  <Loader v-if="isJoining" :size="16" class="spin" />
                  <ArrowRight v-else :size="16" />
                  {{ $t('collaboration.invite.join', 'Join') }}
                </button>
              </div>

              <!-- Step 2: Confirm join -->
              <div v-else class="join-confirm">
                <div class="confirm-info">
                  <span class="confirm-label">{{ $t('collaboration.invite.joinWorkflow', 'Join workflow:') }}</span>
                  <strong class="confirm-name">{{ joinConfirm.workflow_name }}</strong>
                </div>
                <div class="confirm-actions">
                  <button class="btn-cancel" @click="joinConfirm = null" aria-label="Cancel">
                    {{ $t('common.cancel', 'Cancel') }}
                  </button>
                  <button class="join-btn" @click="handleConfirmJoin" :disabled="isJoining">
                    <Loader v-if="isJoining" :size="16" class="spin" />
                    <Check v-else :size="16" />
                    {{ $t('collaboration.invite.confirmJoin', 'Request to Join') }}
                  </button>
                </div>
              </div>

              <!-- Status messages -->
              <p v-if="joinError" class="error-text">{{ joinError }}</p>
              <div v-if="joinStatus === 'pending'" class="pending-notice">
                <Clock :size="14" />
                <span>{{ $t('collaboration.invite.pendingApproval', 'Request sent! Waiting for the owner to approve.') }}</span>
              </div>
            </div>

            <!-- Pro Feature Notice — only shown for owners (who have invite code section) -->
            <div class="pro-notice" v-if="!isPro && (inviteCode || isLoadingCode)">
              <div class="notice-icon">
                <Crown :size="18" />
              </div>
              <div class="notice-content">
                <strong>{{ $t('collaboration.invite.proRequired', 'Pro Feature') }}</strong>
                <p>{{ $t('collaboration.invite.proDescription', 'Upgrade to Pro to enable real-time collaboration with up to 5 team members.') }}</p>
              </div>
              <button class="upgrade-btn" @click="$emit('upgrade')" aria-label="Upgrade">
                {{ $t('common.upgrade', 'Upgrade') }}
              </button>
            </div>

            <!-- Current Participants -->
            <div class="participants-section" v-if="participants.length > 0">
              <label class="section-label">
                <Users :size="16" />
                {{ $t('collaboration.invite.currentParticipants', 'Current Participants') }}
                <span class="count-badge">{{ participants.length }}</span>
              </label>
              <div class="participants-list">
                <div
                  v-for="participant in participants"
                  :key="participant.participantId"
                  class="participant-item"
                >
                  <div class="participant-avatar" :style="{ background: participant.avatarUrl ? 'transparent' : participant.color }">
                    <img
                      v-if="participant.avatarUrl"
                      :src="participant.avatarUrl"
                      :alt="participant.displayName"
                      class="participant-avatar-img"
                    />
                    <template v-else>{{ getInitials(participant.displayName) }}</template>
                  </div>
                  <div class="participant-info">
                    <span class="participant-name">{{ participant.displayName }}</span>
                    <span class="participant-status" :class="participant.presence">
                      {{ getPresenceText(participant.presence) }}
                    </span>
                  </div>
                  <div class="presence-indicator" :class="participant.presence"></div>
                </div>
              </div>
            </div>

            <!-- Instructions -->
            <div class="instructions">
              <h4>{{ $t('collaboration.invite.howItWorks', 'How it works') }}</h4>
              <ol>
                <li>{{ $t('collaboration.invite.step1Code', 'Owner shares the invite code with a team member') }}</li>
                <li>{{ $t('collaboration.invite.step2Code', 'They enter the code and request to join') }}</li>
                <li>{{ $t('collaboration.invite.step3Approve', 'Owner approves the request in the collaboration panel') }}</li>
                <li>{{ $t('collaboration.invite.step4Collab', 'Start collaborating in real-time') }}</li>
              </ol>
            </div>
          </div>

          <!-- Footer -->
          <div class="modal-footer">
            <button class="btn-secondary" @click="$emit('close')" aria-label="Close">
              {{ $t('common.close', 'Close') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { get } from '@/api/client'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { UserPlus, X, Key, Copy, Check, Crown, Users, LogIn, ArrowRight, Loader, Clock } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'

const { t } = useI18n()
const router = useRouter()

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  workflowId: {
    type: String,
    default: ''
  },
  participants: {
    type: Array,
    default: () => []
  },
  isPro: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'upgrade'])

const copied = ref(false)
const joinCode = ref('')
const isJoining = ref(false)
const joinError = ref('')
const joinConfirm = ref(null) // { workflow_id, workflow_name }
const joinStatus = ref('') // '' | 'pending' | 'approved'
const inviteCode = ref('')
const isLoadingCode = ref(false)

// Fetch invite code from backend (requires owner auth)
async function fetchInviteCode() {
  if (!props.workflowId) {
    inviteCode.value = ''
    return
  }

  isLoadingCode.value = true
  try {
    const data = await get(`/collaboration/invite-code/${props.workflowId}`)
    if (data && !data.error) {
      inviteCode.value = data.inviteCode || data.invite_code
    } else {
      inviteCode.value = ''
    }
  } catch {
    inviteCode.value = ''
  } finally {
    isLoadingCode.value = false
  }
}

// Reset state when modal opens
watch(() => props.show, (isOpen) => {
  if (isOpen) {
    copied.value = false
    joinCode.value = ''
    joinError.value = ''
    joinConfirm.value = null
    joinStatus.value = ''
    fetchInviteCode()
  }
})

async function copyCode() {
  if (isLoadingCode.value || !inviteCode.value) return

  try {
    await navigator.clipboard.writeText(inviteCode.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // Fallback: select text for manual copy (clipboard API unavailable in non-HTTPS)
    const el = document.querySelector('[data-invite-code]')
    if (el) { const r = document.createRange(); r.selectNodeContents(el); window.getSelection()?.removeAllRanges(); window.getSelection()?.addRange(r) }
  }
}

// Step 1: Resolve invite code → show confirmation
async function handleResolveCode() {
  if (!joinCode.value.trim()) return

  isJoining.value = true
  joinError.value = ''
  joinConfirm.value = null

  try {
    const code = joinCode.value.trim()
    const data = await get(`/collaboration/resolve-code/${encodeURIComponent(code)}`)

    if (!data || data.error) {
      joinError.value = data?.error || t('collaboration.invite.invalidCode', 'Invalid invite code')
      return
    }
    joinConfirm.value = data // { workflow_id, workflow_name }
  } catch {
    joinError.value = t('collaboration.invite.joinFailed', 'Failed to resolve code. Please try again.')
  } finally {
    isJoining.value = false
  }
}

// Step 2: User confirms → POST /join → pending or approved
async function handleConfirmJoin() {
  if (!joinConfirm.value) return

  isJoining.value = true
  joinError.value = ''

  try {
    const code = joinCode.value.trim()
    const { post: postReq } = await import('@/api/client')
    const res = await postReq('/collaboration/join', { code })

    if (!res || res.error) {
      joinError.value = res?.error || 'Failed to join'
      return
    }

    const data = await res.json()

    if (data.status === 'approved') {
      // Already approved — go to builder
      emit('close')
      router.push({
        path: `/templates/builder/${data.workflow_id}`,
        query: { invite: code },
      })
    } else {
      // Pending — show waiting message
      joinStatus.value = 'pending'
      joinConfirm.value = null
    }
  } catch {
    joinError.value = t('collaboration.invite.joinFailed', 'Failed to join. Please try again.')
  } finally {
    isJoining.value = false
  }
}

function getInitials(name) {
  if (!name) return '?'
  const parts = name.split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}

function getPresenceText(presence) {
  const texts = {
    active: t('collaboration.presence.active', 'Active'),
    idle: t('collaboration.presence.idle', 'Idle'),
    away: t('collaboration.presence.away', 'Away'),
    offline: t('collaboration.presence.offline', 'Offline')
  }
  return texts[presence] || presence
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal-container {
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  border: 1px solid #334155;
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Header */
.modal-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 24px;
  border-bottom: 1px solid #334155;
}

.header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
  border-radius: 12px;
  color: white;
  flex-shrink: 0;
}

.header-text {
  flex: 1;
}

.header-text h2 {
  font-size: 18px;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0;
}

.header-text p {
  font-size: 13px;
  color: #94a3b8;
  margin: 4px 0 0 0;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #f1f5f9;
}

/* Content */
.modal-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
}

.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: rgba(139, 92, 246, 0.2);
  border-radius: 10px;
  font-size: 11px;
  color: #a78bfa;
}

/* Invite Code Section */
.invite-code-section {
  margin-bottom: 24px;
}

.code-display {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(139, 92, 246, 0.05) 100%);
  border: 2px dashed rgba(139, 92, 246, 0.4);
  border-radius: 12px;
}

.code-value {
  flex: 1;
  font-size: 28px;
  font-weight: 800;
  font-family: 'Fira Code', monospace;
  color: #a78bfa;
  letter-spacing: 0.1em;
  cursor: pointer;
  user-select: all;
  display: flex;
  align-items: center;
}

.code-value.loading {
  justify-content: center;
  cursor: default;
}

.copy-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: rgba(139, 92, 246, 0.2);
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 10px;
  color: #a78bfa;
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn:hover {
  background: rgba(139, 92, 246, 0.3);
  transform: scale(1.05);
}

.helper-text {
  font-size: 12px;
  color: #64748b;
  margin-top: 10px;
}

/* Join Section */
.join-section {
  margin-bottom: 24px;
  padding: 20px;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 12px;
}

.join-input-group {
  display: flex;
  gap: 8px;
}

.join-input {
  flex: 1;
  padding: 12px 16px;
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid #334155;
  border-radius: 10px;
  font-size: 15px;
  font-family: 'Fira Code', monospace;
  color: #e2e8f0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  outline: none;
}

.join-input::placeholder {
  text-transform: none;
  letter-spacing: normal;
  color: #475569;
}

.join-input:focus {
  border-color: #8b5cf6;
}

.join-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
  border: none;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.join-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.join-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.error-text {
  font-size: 12px;
  color: #ef4444;
  margin-top: 8px;
}

/* Join Confirmation */
.join-confirm {
  padding: 14px;
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.25);
  border-radius: 10px;
}

.confirm-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 14px;
}

.confirm-label {
  font-size: 12px;
  color: #94a3b8;
}

.confirm-name {
  font-size: 16px;
  color: #f1f5f9;
}

.confirm-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.btn-cancel {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #475569;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: rgba(71, 85, 105, 0.3);
  color: #f1f5f9;
}

/* Pending Notice */
.pending-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 14px;
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.25);
  border-radius: 8px;
  font-size: 12px;
  color: #fbbf24;
}

/* Pro Notice */
.pro-notice {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(251, 191, 36, 0.05) 100%);
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 12px;
  margin-bottom: 24px;
}

.notice-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: rgba(245, 158, 11, 0.2);
  border-radius: 8px;
  color: #f59e0b;
  flex-shrink: 0;
}

.notice-content {
  flex: 1;
}

.notice-content strong {
  display: block;
  font-size: 13px;
  color: #f59e0b;
  margin-bottom: 2px;
}

.notice-content p {
  font-size: 12px;
  color: #94a3b8;
  margin: 0;
  line-height: 1.4;
}

.upgrade-btn {
  padding: 8px 16px;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border: none;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.upgrade-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
}

/* Participants Section */
.participants-section {
  margin-bottom: 24px;
}

.participants-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.participant-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 10px;
}

.participant-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
  overflow: hidden;
}

.participant-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.participant-info {
  flex: 1;
  min-width: 0;
}

.participant-name {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #f1f5f9;
}

.participant-status {
  font-size: 11px;
}

.participant-status.active { color: #22c55e; }
.participant-status.idle { color: #eab308; }
.participant-status.away { color: #f97316; }
.participant-status.offline { color: #64748b; }

.presence-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.presence-indicator.active { background: #22c55e; }
.presence-indicator.idle { background: #eab308; }
.presence-indicator.away { background: #f97316; }
.presence-indicator.offline { background: #64748b; }

/* Instructions */
.instructions {
  padding: 16px;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 12px;
}

.instructions h4 {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  margin: 0 0 12px 0;
}

.instructions ol {
  margin: 0;
  padding-left: 20px;
}

.instructions li {
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.6;
  margin-bottom: 4px;
}

.instructions li:last-child {
  margin-bottom: 0;
}

/* Footer */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #334155;
}

.btn-secondary {
  padding: 10px 20px;
  background: transparent;
  border: 1px solid #475569;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: rgba(71, 85, 105, 0.3);
  color: #f1f5f9;
}

/* Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95) translateY(20px);
}
</style>

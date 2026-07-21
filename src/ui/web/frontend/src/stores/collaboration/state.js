/**
 * Collaboration Store — State & Getters
 *
 * All reactive state refs and computed getters for the collaboration store.
 */

import { ref, computed } from 'vue'

export function useCollaborationState() {
  // ========== State ==========

  // Session
  const sessionId = ref(null)
  const documentId = ref(null)
  const workflowId = ref(null)
  const isConnected = ref(false)
  const isConnecting = ref(false)

  // Participants
  const participants = ref([])
  const currentParticipantId = ref(null)

  // Cursors
  const cursors = ref({}) // participantId -> { x, y, path }

  // Node Locks (CRDT Phase 1)
  const nodeLocks = ref({}) // nodeId -> { userId, userName, acquiredAt }
  const pendingLockRequests = ref(new Set()) // nodeIds waiting for lock response

  // Chat Messages (persistent, stored in Firestore)
  const chatMessages = ref([])
  const chatLoaded = ref(false)

  // Incoming workflow sync (from other participants)
  const incomingWorkflowUpdate = ref(null)

  // Quota Info (for free users with time-based limits)
  const quotaInfo = ref({
    isUnlimited: true,
    remainingHours: null,
    remainingMinutes: null
  })

  // Owner info
  const isOwner = ref(false)

  // Session terminated by owner (prevents auto-reconnect)
  const sessionTerminated = ref(false)

  // WebSocket
  const ws = ref(null)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5
  const reconnectTimeout = ref(null)
  const error = ref(null)
  const lastUser = ref(null)  // Store user info for reconnection

  // ========== Getters ==========

  const isActive = computed(() => isConnected.value && sessionId.value !== null)

  const otherParticipants = computed(() => {
    return participants.value.filter(p => p.participant_id !== currentParticipantId.value)
  })

  const activeParticipants = computed(() => {
    return participants.value.filter(p => p.presence === 'active')
  })

  const otherCursors = computed(() => {
    const result = {}
    for (const [pid, cursor] of Object.entries(cursors.value)) {
      if (pid !== currentParticipantId.value) {
        const participant = participants.value.find(p => p.participantId === pid || p.userId === pid)
        if (participant) {
          result[pid] = {
            x: cursor.x, y: cursor.y, lastUpdate: cursor.lastUpdate,
            displayName: participant.displayName, color: participant.color,
          }
        }
      }
    }
    return result
  })

  // Check if a node is locked by someone else (owner can override)
  const isNodeLockedByOther = computed(() => (nodeId) => {
    if (isOwner.value) return false  // Owner can always edit
    const lock = nodeLocks.value[nodeId]
    if (!lock) return false
    return lock.userId !== lastUser.value?.id
  })

  // Get lock info for a node
  const getNodeLock = computed(() => (nodeId) => {
    return nodeLocks.value[nodeId] || null
  })

  // Check if current user has lock on a node
  const hasLockOn = computed(() => (nodeId) => {
    const lock = nodeLocks.value[nodeId]
    if (!lock) return false
    return lock.userId === lastUser.value?.id
  })

  return {
    // State
    sessionId,
    documentId,
    workflowId,
    isConnected,
    isConnecting,
    participants,
    currentParticipantId,
    cursors,
    nodeLocks,
    pendingLockRequests,
    chatMessages,
    chatLoaded,
    incomingWorkflowUpdate,
    quotaInfo,
    isOwner,
    sessionTerminated,
    ws,
    reconnectAttempts,
    maxReconnectAttempts,
    reconnectTimeout,
    error,
    lastUser,

    // Getters
    isActive,
    otherParticipants,
    activeParticipants,
    otherCursors,
    isNodeLockedByOther,
    getNodeLock,
    hasLockOn,
  }
}

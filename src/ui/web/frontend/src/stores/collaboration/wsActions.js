/**
 * Collaboration Store — WebSocket Actions
 *
 * WebSocket connect / disconnect / message handling actions.
 */

import { moatTelemetry, moatTimer } from '@/services/moatTelemetry'
import { post } from '@/api/client'

/**
 * Generate a consistent color for a user
 */
export function generateUserColor(userId) {
  const colors = [
    '#3b82f6', '#ef4444', '#22c55e', '#f59e0b',
    '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6'
  ]
  let hash = 0
  for (let i = 0; i < userId.length; i++) {
    hash = ((hash << 5) - hash) + userId.charCodeAt(i)
    hash = hash & hash
  }
  return colors[Math.abs(hash) % colors.length]
}

/**
 * Map backend participant data to frontend format
 */
export function mapParticipant(p) {
  return {
    participantId: p.user_id || p.participant_id,
    userId: p.user_id || p.participant_id,
    displayName: p.user_name || p.display_name || p.displayName || '',
    avatarUrl: p.user_avatar || p.avatar_url || p.avatarUrl || null,
    color: p.color || '#3B82F6',
    cursor: p.cursor_x != null && p.cursor_y != null ? { x: p.cursor_x, y: p.cursor_y } : null,
    selectedNode: p.selected_node || p.selectedNode || null,
    editingNode: p.editing_node || p.editingNode || null,
    presence: p.presence || 'active',
    lastSeen: p.last_seen || p.lastSeen || new Date().toISOString()
  }
}

/**
 * Create WebSocket action functions.
 * @param {Object} state - All state refs from useCollaborationState()
 * @param {Object} deps - { loadChatHistory, releaseAllLocks } injected by index
 */
export function useWsActions(state, deps) {
  const {
    sessionId, documentId, workflowId, isConnected, isConnecting,
    participants, currentParticipantId, cursors, nodeLocks,
    pendingLockRequests, chatMessages, chatLoaded,
    incomingWorkflowUpdate, quotaInfo, isOwner, sessionTerminated,
    ws, reconnectAttempts, maxReconnectAttempts, reconnectTimeout,
    error, lastUser,
  } = state

  /**
   * Send a message to the WebSocket
   */
  function sendMessage(message) {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify(message))
    }
  }

  /**
   * Add a participant
   */
  function addParticipant(participant) {
    const mapped = mapParticipant(participant)
    const existing = participants.value.find(p => p.participantId === mapped.participantId)
    if (!existing) {
      participants.value.push(mapped)
    }
  }

  /**
   * Remove a participant
   */
  function removeParticipant(participantId) {
    participants.value = participants.value.filter(p => p.participantId !== participantId && p.userId !== participantId)
    delete cursors.value[participantId]
  }

  /**
   * Update participant presence
   */
  function updateParticipantPresence(participantId, presence) {
    const participant = participants.value.find(p => p.participantId === participantId || p.userId === participantId)
    if (participant) {
      participant.presence = presence
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  function handleMessage(message) {
    switch (message.type) {
      case 'join_ack':
        sessionId.value = message.payload.session_id
        documentId.value = message.payload.document_id
        currentParticipantId.value = message.payload.participant_id
        participants.value = (message.payload.participants || []).map(mapParticipant)
        if (message.payload.locks) {
          for (const lock of message.payload.locks) {
            nodeLocks.value[lock.node_id] = {
              userId: lock.user_id,
              userName: lock.user_name,
              acquiredAt: lock.acquired_at
            }
          }
        }
        break

      case 'participant_joined':
        addParticipant(message.payload)
        break

      case 'participant_left':
        removeParticipant(message.payload.participant_id)
        break

      case 'join':
        addParticipant(message.user)
        break

      case 'leave':
        removeParticipant(message.user_id)
        break

      case 'presence':
        updateParticipantPresence(message.payload.participant_id, message.payload.presence)
        break

      case 'presence.update': {
        const user = message.user
        if (!user || user.user_id === currentParticipantId.value) break
        const participant = participants.value.find(
          p => p.participantId === user.user_id || p.userId === user.user_id
        )
        if (participant) {
          participant.lastSeen = user.last_seen
          participant.selectedNode = user.selected_node || null
          participant.editingNode = user.editing_node || null
          if (user.cursor_x != null && user.cursor_y != null) {
            participant.cursor = { x: user.cursor_x, y: user.cursor_y }
          }
        }
        if (user.cursor_x != null && user.cursor_y != null) {
          cursors.value = {
            ...cursors.value,
            [user.user_id]: { x: user.cursor_x, y: user.cursor_y, lastUpdate: Date.now() }
          }
        }
        break
      }

      // ========== Lock Messages (CRDT Phase 1) ==========

      case 'presence.list':
        if (message.session_id) {
          sessionId.value = message.session_id
        }
        participants.value = (message.users || []).map(mapParticipant)
        if (message.locks) {
          for (const lock of message.locks) {
            nodeLocks.value[lock.node_id] = {
              userId: lock.user_id,
              userName: lock.user_name,
              acquiredAt: lock.acquired_at
            }
          }
        }
        deps.loadChatHistory()
        break

      case 'lock.granted':
        nodeLocks.value[message.node_id] = {
          userId: message.user_id,
          userName: message.user_name,
          acquiredAt: new Date().toISOString()
        }
        pendingLockRequests.value.delete(message.node_id)
        break

      case 'lock.denied':
        pendingLockRequests.value.delete(message.node_id)
        break

      case 'lock.release':
        delete nodeLocks.value[message.node_id]
        break

      case 'lock.expired':
        delete nodeLocks.value[message.node_id]
        break

      // ========== CRDT Sync (Phase 2) ==========

      case 'yjs.sync':
      case 'yjs.update':
        break

      // ========== Workflow Sync ==========

      case 'node.updated':
      case 'workflow.updated':
        if (message.changes?.elements) {
          incomingWorkflowUpdate.value = {
            elements: message.changes.elements,
            userId: message.user_id,
            timestamp: Date.now(),
          }
        }
        break

      // ========== Member Events ==========

      case 'session.terminated':
        error.value = message.message || 'The owner ended the collaboration session.'
        sessionTerminated.value = true
        if (ws.value) {
          try { ws.value.close(1000) } catch {}
          ws.value = null
        }
        isConnected.value = false
        if (reconnectTimeout.value) {
          clearTimeout(reconnectTimeout.value)
          reconnectTimeout.value = null
        }
        reconnectAttempts.value = maxReconnectAttempts
        break

      // ========== Chat Messages (Persistent) ==========

      case 'chat.message':
        chatMessages.value.push({
          id: message.message_id,
          senderId: message.sender_id,
          senderName: message.sender_name,
          senderAvatar: message.sender_avatar,
          content: message.content,
          createdAt: message.created_at,
        })
        break

      // ========== Quota Info ==========

      case 'quota_info':
        quotaInfo.value = {
          isUnlimited: message.is_unlimited || false,
          remainingHours: message.remaining_hours || null,
          remainingMinutes: message.remaining_minutes || null
        }
        break

      // ========== Error Messages ==========

      case 'error':
        error.value = message.message || 'Connection error'
        if (message.code === 'NOT_AUTHORIZED') {
          moatTelemetry.trackFriction('collaboration', 'auth', 'NOT_AUTHORIZED', {
            workflow_id: workflowId.value,
          })
        } else if (message.code === 'QUOTA_EXCEEDED' || message.code === 'FEATURE_DISABLED') {
          moatTelemetry.trackFriction('collaboration', 'quota', message.code, {
            workflow_id: workflowId.value,
            upgrade_url: message.upgrade_url
          })
        }
        break

      default:
        break
    }
  }

  /**
   * Handle WebSocket disconnect (reconnect with exponential backoff)
   */
  function handleDisconnect() {
    if (reconnectAttempts.value < maxReconnectAttempts && workflowId.value && lastUser.value) {
      reconnectAttempts.value++
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 30000)

      moatTelemetry.trackCollabReconnect(workflowId.value, reconnectAttempts.value, false)

      reconnectTimeout.value = setTimeout(() => {
        if (workflowId.value && lastUser.value) {
          joinSession(workflowId.value, lastUser.value).then(() => {
            moatTelemetry.trackCollabReconnect(workflowId.value, reconnectAttempts.value, true)
          })
        }
      }, delay)
    } else if (reconnectAttempts.value >= maxReconnectAttempts) {
      error.value = 'Connection lost. Please refresh the page.'
      moatTelemetry.trackFriction('collaboration', 'reconnect', 'max_attempts_reached', {
        workflow_id: workflowId.value,
        attempts: reconnectAttempts.value
      })
      console.error('Collaboration: Max reconnect attempts reached')
    }
  }

  /**
   * Join a collaboration session
   */
  async function joinSession(wfId, user, options = {}) {
    if (isConnecting.value) return
    if (!wfId || !user?.id) {
      error.value = 'Invalid workflow ID or user'
      return
    }

    isConnecting.value = true
    workflowId.value = wfId
    lastUser.value = user
    isOwner.value = !!options.isOwner
    error.value = null

    const selfParticipant = mapParticipant({
      user_id: user.id,
      user_name: user.name || user.displayName || user.email || 'Anonymous',
      user_avatar: user.avatarUrl || user.avatar_url || user.photoURL || null,
      color: generateUserColor(user.id),
      presence: 'active'
    })
    participants.value = [selfParticipant]
    currentParticipantId.value = user.id

    if (reconnectTimeout.value) {
      clearTimeout(reconnectTimeout.value)
      reconnectTimeout.value = null
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const params = new URLSearchParams({
        user_id: user.id,
        user_name: user.name || user.displayName || user.email || 'Anonymous',
        user_avatar: user.avatarUrl || user.avatar_url || user.photoURL || '',
        is_pro: user.is_pro ? 'true' : 'false'
      })
      const wsUrl = `${protocol}//${window.location.host}/ws/collaboration/${wfId}?${params}`

      ws.value = new WebSocket(wsUrl)

      ws.value.onopen = () => {
        isConnected.value = true
        isConnecting.value = false
        reconnectAttempts.value = 0
        error.value = null

        moatTelemetry.trackCollabJoin(wfId, null, 1)
        moatTimer.start(`collab_session_${wfId}`)

        sendMessage({
          type: 'join',
          payload: {
            user_id: user.id,
            display_name: user.name || user.displayName || user.email || 'Anonymous',
            avatar_url: user.avatarUrl || user.avatar_url || user.photoURL || null,
            color: generateUserColor(user.id)
          }
        })
      }

      ws.value.onmessage = (event) => {
        try {
          handleMessage(JSON.parse(event.data))
        } catch (e) {
          console.error('Failed to parse collaboration message:', e)
        }
      }

      ws.value.onclose = (event) => {
        isConnected.value = false
        isConnecting.value = false
        // 1000 = normal close, 4003 = forbidden, 4008 = session limit
        // 4503 = worker not configured (no real-time, fall back to REST)
        if (event.code === 4503) {
          error.value = 'Real-time collaboration unavailable — worker not connected'
          // Still load chat history via REST so messages are visible
          deps.loadChatHistory?.()
          return
        }
        if (event.code !== 1000 && event.code !== 4003 && event.code !== 4008) {
          handleDisconnect()
        }
      }

      ws.value.onerror = (err) => {
        console.error('Collaboration WebSocket error:', err)
        error.value = 'Connection failed'
        isConnecting.value = false
      }
    } catch (err) {
      error.value = err.message || 'Failed to connect'
      isConnecting.value = false
    }
  }

  /**
   * Leave the current session
   */
  function leaveSession() {
    const wfId = workflowId.value
    if (wfId) {
      const duration = moatTimer.end(`collab_session_${wfId}`)
      moatTelemetry.trackCollabLeave(wfId, sessionId.value, duration)
    }

    deps.releaseAllLocks()

    if (reconnectTimeout.value) {
      clearTimeout(reconnectTimeout.value)
      reconnectTimeout.value = null
    }

    if (ws.value) {
      try {
        sendMessage({ type: 'leave' })
        ws.value.close(1000, 'User left')
      } catch (e) {
        // Ignore errors during cleanup
      }
      ws.value = null
    }

    // Reset state
    sessionId.value = null
    documentId.value = null
    workflowId.value = null
    participants.value = []
    cursors.value = {}
    nodeLocks.value = {}
    pendingLockRequests.value = new Set()
    chatMessages.value = []
    chatLoaded.value = false
    incomingWorkflowUpdate.value = null
    isConnected.value = false
    isConnecting.value = false
    currentParticipantId.value = null
    reconnectAttempts.value = 0
    error.value = null
    lastUser.value = null
    isOwner.value = false
    sessionTerminated.value = false
  }

  /**
   * Terminate the session (owner only).
   */
  async function terminateSession() {
    if (!isOwner.value || !workflowId.value) return

    try {
      await post(`/collaboration/${workflowId.value}/terminate`)
    } catch {
      // Still leave locally
    }
    leaveSession()
  }

  /**
   * Broadcast cursor position (flow coordinates)
   */
  function broadcastCursor(x, y) {
    sendMessage({ type: 'cursor.move', x, y })
  }

  /**
   * Broadcast an operation
   */
  function broadcastOperation(operation) {
    sendMessage({
      type: 'operation',
      payload: { operation }
    })
  }

  /**
   * Broadcast workflow elements update to other participants (debounced).
   */
  let _workflowBroadcastTimer = null
  function broadcastWorkflowUpdate(elements) {
    if (!isConnected.value) return
    if (_workflowBroadcastTimer) clearTimeout(_workflowBroadcastTimer)
    _workflowBroadcastTimer = setTimeout(() => {
      sendMessage({
        type: 'workflow.updated',
        changes: { elements },
      })
    }, 300)
  }

  return {
    sendMessage,
    handleMessage,
    handleDisconnect,
    joinSession,
    leaveSession,
    terminateSession,
    broadcastCursor,
    broadcastOperation,
    broadcastWorkflowUpdate,
  }
}

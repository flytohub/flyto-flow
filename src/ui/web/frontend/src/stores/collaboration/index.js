/**
 * Collaboration Store
 *
 * Manages real-time collaboration state using CRDT.
 * This is a key moat feature - n8n does not support this.
 *
 * Composed from:
 *   state.js       — State refs + computed getters
 *   wsActions.js   — WebSocket connect/disconnect/message handling
 *   chatActions.js — Chat message send/receive
 *   lockActions.js — Node lock acquire/release/refresh
 */

import { defineStore } from 'pinia'
import { useCollaborationState } from './state'
import { useWsActions } from './wsActions'
import { useChatActions } from './chatActions'
import { useLockActions } from './lockActions'

export const useCollaborationStore = defineStore('collaboration', () => {
  // 1. State & getters
  const state = useCollaborationState()

  // 2. Lock actions (needs sendMessage — resolved via deps below)
  let _sendMessage = null
  const lockActions = useLockActions(state, {
    get sendMessage() { return _sendMessage }
  })

  // 3. Chat actions (needs sendMessage)
  const chatActions = useChatActions(state, {
    get sendMessage() { return _sendMessage }
  })

  // 4. WS actions (needs loadChatHistory + releaseAllLocks)
  const wsActions = useWsActions(state, {
    loadChatHistory: chatActions.loadChatHistory,
    releaseAllLocks: lockActions.releaseAllLocks,
  })

  // Resolve circular dep: lock & chat actions need sendMessage from wsActions
  _sendMessage = wsActions.sendMessage

  return {
    // State
    sessionId: state.sessionId,
    documentId: state.documentId,
    workflowId: state.workflowId,
    isConnected: state.isConnected,
    isConnecting: state.isConnecting,
    participants: state.participants,
    currentParticipantId: state.currentParticipantId,
    cursors: state.cursors,
    nodeLocks: state.nodeLocks,
    chatMessages: state.chatMessages,
    quotaInfo: state.quotaInfo,
    error: state.error,
    reconnectAttempts: state.reconnectAttempts,

    // Getters
    isActive: state.isActive,
    otherParticipants: state.otherParticipants,
    activeParticipants: state.activeParticipants,
    otherCursors: state.otherCursors,
    isNodeLockedByOther: state.isNodeLockedByOther,
    getNodeLock: state.getNodeLock,
    hasLockOn: state.hasLockOn,

    // WS Actions
    joinSession: wsActions.joinSession,
    leaveSession: wsActions.leaveSession,
    terminateSession: wsActions.terminateSession,
    sendMessage: wsActions.sendMessage,
    broadcastCursor: wsActions.broadcastCursor,
    broadcastOperation: wsActions.broadcastOperation,
    broadcastWorkflowUpdate: wsActions.broadcastWorkflowUpdate,
    incomingWorkflowUpdate: state.incomingWorkflowUpdate,

    // Chat Actions
    loadChatHistory: chatActions.loadChatHistory,
    sendChatMessage: chatActions.sendChatMessage,

    // Owner
    isOwner: state.isOwner,
    sessionTerminated: state.sessionTerminated,

    // Lock Actions (CRDT Phase 1)
    acquireLock: lockActions.acquireLock,
    releaseLock: lockActions.releaseLock,
    releaseAllLocks: lockActions.releaseAllLocks,
    canEditNode: lockActions.canEditNode,
  }
})

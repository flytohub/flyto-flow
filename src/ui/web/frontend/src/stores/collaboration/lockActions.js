/**
 * Collaboration Store — Lock Actions
 *
 * Node lock acquire / release / refresh actions (CRDT Phase 1).
 */

/**
 * Create lock action functions.
 * @param {Object} state - All state refs from useCollaborationState()
 * @param {Object} deps - { sendMessage } injected by index
 */
export function useLockActions(state, deps) {
  const { isConnected, isOwner, nodeLocks, pendingLockRequests, lastUser } = state

  /**
   * Request a lock on a node before editing
   * @param {string} nodeId - The node ID to lock
   * @returns {Promise<boolean>} - True if lock was granted
   */
  async function acquireLock(nodeId) {
    if (!isConnected.value || !nodeId) return false

    // Check if we already have the lock
    const existingLock = nodeLocks.value[nodeId]
    if (existingLock && existingLock.userId === lastUser.value?.id) {
      return true
    }

    // Check if someone else has the lock
    if (existingLock && existingLock.userId !== lastUser.value?.id) {
      return false
    }

    // Track pending request
    pendingLockRequests.value.add(nodeId)

    // Request the lock
    deps.sendMessage({
      type: 'lock.acquire',
      node_id: nodeId
    })

    // Wait for response (with timeout)
    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        pendingLockRequests.value.delete(nodeId)
        resolve(false)
      }, 5000) // 5 second timeout

      const checkLock = setInterval(() => {
        if (!pendingLockRequests.value.has(nodeId)) {
          clearInterval(checkLock)
          clearTimeout(timeout)
          // Check if we got the lock
          const lock = nodeLocks.value[nodeId]
          resolve(lock && lock.userId === lastUser.value?.id)
        }
      }, 50)
    })
  }

  /**
   * Release a lock on a node
   * @param {string} nodeId - The node ID to unlock
   */
  function releaseLock(nodeId) {
    if (!isConnected.value || !nodeId) return

    // Only release if we own it
    const lock = nodeLocks.value[nodeId]
    if (!lock || lock.userId !== lastUser.value?.id) return

    deps.sendMessage({
      type: 'lock.release',
      node_id: nodeId
    })
  }

  /**
   * Release all locks held by current user
   */
  function releaseAllLocks() {
    if (!isConnected.value) return

    for (const [nodeId, lock] of Object.entries(nodeLocks.value)) {
      if (lock.userId === lastUser.value?.id) {
        deps.sendMessage({
          type: 'lock.release',
          node_id: nodeId
        })
      }
    }
  }

  /**
   * Check if a node can be edited (not locked by someone else)
   * @param {string} nodeId - The node ID to check
   * @returns {boolean}
   */
  function canEditNode(nodeId) {
    if (isOwner.value) return true  // Owner can always edit
    const lock = nodeLocks.value[nodeId]
    if (!lock) return true
    return lock.userId === lastUser.value?.id
  }

  return {
    acquireLock,
    releaseLock,
    releaseAllLocks,
    canEditNode,
  }
}

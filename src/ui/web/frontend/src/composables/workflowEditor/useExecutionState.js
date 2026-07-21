/**
 * Execution State Composable
 * Manages workflow execution state tracking for canvas nodes
 *
 * S-Grade Architecture: Frontend only renders, backend computes all states
 */

import { watch, toRefs, onUnmounted } from 'vue'

export function useExecutionState(nodes, edges, props) {
  // Backend-computed node states (required)
  const executionNodeStates = props.executionNodeStates
    ? toRefs(props).executionNodeStates
    : null

  // Agent real-time activity (optional)
  const agentActivity = props.agentActivity
    ? toRefs(props).agentActivity
    : null

  // Store watcher cleanup functions
  let stopWatcher = null
  let stopAgentWatcher = null

  // Watch execution state changes and update node data
  function setupExecutionWatcher() {
    if (!executionNodeStates) {
      return { stop: () => {} }
    }

    // Optimized: Iterate keys manually instead of deep watch for better performance
    stopWatcher = watch(executionNodeStates, (nodeStates) => {
      // No nodeStates = not executing, clear all states
      if (!nodeStates || Object.keys(nodeStates).length === 0) {
        nodes.value.forEach(n => {
          if (n.data && n.data.executionState !== null) {
            n.data.executionState = null
            n.data.agentActivity = null
          }
        })
        return
      }

      // Update each node's executionState (only if changed)
      nodes.value.forEach(node => {
        const state = nodeStates[node.id] || null
        if (!node.data) node.data = {}
        if (node.data.executionState !== state) {
          node.data.executionState = state
        }
      })
    }, { deep: true, immediate: true })

    // Watch agent activity and inject into node data
    if (agentActivity) {
      stopAgentWatcher = watch(agentActivity, (activity) => {
        nodes.value.forEach(node => {
          if (!node.data) node.data = {}
          const nodeActivity = activity?.[node.id] || null
          if (node.data.agentActivity !== nodeActivity) {
            node.data.agentActivity = nodeActivity
          }
        })
      }, { deep: true, immediate: true })
    }

    // Cleanup watchers on unmount to prevent memory leak (S1 fix)
    onUnmounted(() => {
      if (stopWatcher) { stopWatcher(); stopWatcher = null }
      if (stopAgentWatcher) { stopAgentWatcher(); stopAgentWatcher = null }
    })

    return { stop: stopWatcher }
  }

  return {
    setupExecutionWatcher
  }
}

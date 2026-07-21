/**
 * Replay Utils Composable
 *
 * Utility functions for the replay panel.
 */

export function useReplayUtils() {
  /**
   * Format duration between two timestamps
   */
  function formatDuration(startTime, endTime) {
    if (!startTime || !endTime) return '—'
    const start = new Date(startTime)
    const end = new Date(endTime)
    const ms = end - start
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  /**
   * Format timestamp as relative time
   */
  function formatTimeAgo(timestamp) {
    if (!timestamp) return ''
    const seconds = Math.floor((new Date() - new Date(timestamp)) / 1000)

    if (seconds < 60) return 'just now'
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    return `${Math.floor(seconds / 86400)}d ago`
  }

  /**
   * Format result preview for display
   */
  function formatResult(result) {
    if (!result) return '-'
    if (typeof result === 'string') return result
    const json = JSON.stringify(result, null, 2)
    return json.length > 100 ? json.substring(0, 100) + '...' : json
  }

  return {
    formatDuration,
    formatTimeAgo,
    formatResult
  }
}

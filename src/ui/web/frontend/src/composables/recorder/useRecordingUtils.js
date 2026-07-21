/**
 * Recording Utilities Composable
 *
 * Utility functions for the recording panel.
 */

export function useRecordingUtils() {
  /**
   * Format duration as MM:SS
   */
  function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  /**
   * Format action type for display
   */
  function formatActionType(type) {
    const typeMap = {
      click: 'Click',
      fill: 'Type',
      select: 'Select',
      check: 'Check',
      hover: 'Hover',
      press: 'Key',
      navigate: 'Go To',
      wait: 'Wait',
      screenshot: 'Screenshot',
      assert: 'Assert'
    }
    return typeMap[type] || type
  }

  /**
   * Truncate string with ellipsis
   */
  function truncate(str, length) {
    if (str.length <= length) return str
    return str.substring(0, length) + '...'
  }

  /**
   * Check if action type needs a value field
   */
  function needsValue(type) {
    return ['fill', 'select', 'press', 'navigate', 'wait'].includes(type)
  }

  return {
    formatDuration,
    formatActionType,
    truncate,
    needsValue
  }
}

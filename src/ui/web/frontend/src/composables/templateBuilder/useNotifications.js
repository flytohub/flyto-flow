/**
 * Notifications Composable for TemplateBuilder
 * Wraps global useToast and useConfirm for TemplateBuilder-specific usage
 */
import { useToast } from '../useToast'
import { useConfirm } from '../useConfirm'
import { DEFAULTS } from '@/config/defaults'

export function useNotifications() {
  const toast = useToast()
  const confirm = useConfirm()

  /**
   * Show confirm dialog
   * @param {Object} options - Dialog options
   * @param {string} options.type - Dialog type ('warning' | 'danger')
   * @param {string} options.title - Dialog title
   * @param {string} options.message - Dialog message
   * @param {string} options.confirmText - Confirm button text
   * @returns {Promise<boolean>} Whether confirmed
   */
  function showConfirm(options) {
    return confirm.show(options)
  }

  /**
   * Execute confirm action (for ConfirmDialog component)
   */
  function executeConfirm() {
    confirm.confirm()
  }

  /**
   * Cancel confirm dialog (for ConfirmDialog component)
   */
  function cancelConfirm() {
    confirm.cancel()
  }

  /**
   * Show toast notification
   * @param {string} message - Toast message
   * @param {string} type - Toast type ('success' | 'error' | 'warning' | 'info')
   * @param {number} duration - Duration in ms (default 3000)
   */
  function showToast(message, type = 'success', duration = DEFAULTS.TIMING.TOAST_DURATION) {
    toast.show(message, type, duration)
  }

  return {
    // Confirm dialog - expose state for ConfirmDialog component
    confirmDialog: confirm.state,

    // Toast - expose state for ToastNotification component
    toast: {
      show: false, // Deprecated: Use global ToastContainer instead
      type: 'success',
      message: ''
    },

    // Confirm dialog methods
    showConfirm,
    executeConfirm,
    cancelConfirm,

    // Toast methods
    showToast
  }
}

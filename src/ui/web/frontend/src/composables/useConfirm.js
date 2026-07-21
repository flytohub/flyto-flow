/**
 * Global Confirm Dialog System
 * Singleton pattern for app-wide confirmation dialogs
 */
import { reactive, readonly } from 'vue'

const state = reactive({
  show: false,
  type: 'warning',
  title: '',
  message: '',
  confirmText: '',
  cancelText: '',
  resolve: null
})

/**
 * Show a confirmation dialog
 * @param {Object} options - Dialog options
 * @param {string} options.title - Dialog title
 * @param {string} options.message - Dialog message
 * @param {string} options.type - Dialog type: 'warning' | 'danger' | 'info'
 * @param {string} options.confirmText - Confirm button text
 * @param {string} options.cancelText - Cancel button text
 * @returns {Promise<boolean>} Whether user confirmed
 */
function show(options) {
  return new Promise((resolve) => {
    state.show = true
    state.type = options.type || 'warning'
    state.title = options.title || ''
    state.message = options.message || ''
    state.confirmText = options.confirmText || 'Confirm'
    state.cancelText = options.cancelText || 'Cancel'
    state.resolve = resolve
  })
}

/**
 * Confirm the dialog
 */
function confirm() {
  if (state.resolve) {
    state.resolve(true)
  }
  close()
}

/**
 * Cancel the dialog
 */
function cancel() {
  if (state.resolve) {
    state.resolve(false)
  }
  close()
}

/**
 * Close the dialog
 */
function close() {
  state.show = false
  state.resolve = null
}

export function useConfirm() {
  return {
    state: readonly(state),
    show,
    confirm,
    cancel,
    close
  }
}

/**
 * Global Toast Notification System
 * Singleton pattern for app-wide toast notifications
 */
import { reactive, readonly } from 'vue'
import { DEFAULTS } from '../config/defaults'

const state = reactive({
  toasts: []
})

let toastId = 0

/**
 * Add a toast notification
 * @param {string} message - Toast message
 * @param {string} type - Toast type: 'success' | 'error' | 'warning' | 'info'
 * @param {number} duration - Duration in ms (0 for persistent)
 * @returns {number} Toast ID for manual dismissal
 */
function show(message, type = 'info', duration = null) {
  const id = ++toastId
  const defaultDuration = type === 'error'
    ? DEFAULTS.TIMING.TOAST_DURATION_ERROR
    : DEFAULTS.TIMING.TOAST_DURATION

  const toast = {
    id,
    message,
    type,
    duration: duration ?? defaultDuration
  }

  state.toasts.push(toast)

  if (toast.duration > 0) {
    setTimeout(() => dismiss(id), toast.duration)
  }

  return id
}

/**
 * Dismiss a toast by ID
 * @param {number} id - Toast ID
 */
function dismiss(id) {
  const index = state.toasts.findIndex(t => t.id === id)
  if (index !== -1) {
    state.toasts.splice(index, 1)
  }
}

/**
 * Dismiss all toasts
 */
function dismissAll() {
  state.toasts.splice(0, state.toasts.length)
}

/**
 * Shorthand methods
 */
const success = (message, duration) => show(message, 'success', duration)
const error = (message, duration) => show(message, 'error', duration)
const warning = (message, duration) => show(message, 'warning', duration)
const info = (message, duration) => show(message, 'info', duration)

export function useToast() {
  return {
    toasts: readonly(state).toasts,
    show,
    dismiss,
    dismissAll,
    success,
    error,
    warning,
    info
  }
}

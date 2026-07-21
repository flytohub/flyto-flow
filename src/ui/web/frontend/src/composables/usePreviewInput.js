import { ref, watch, onUnmounted } from 'vue'
import { DEFAULTS } from '@/config/defaults'

export function usePreviewInput(props, emit, options = {}) {
  const {
    defaultValue = '',
    valueKey = 'default',
    immediate = false
  } = options

  const localValue = ref(props.component?.[valueKey] ?? defaultValue)
  const isFocused = ref(false)
  let debounceTimer = null

  watch(
    () => props.component?.[valueKey],
    (newVal) => {
      if (!isFocused.value) {
        localValue.value = newVal ?? defaultValue
      }
    }
  )

  function emitUpdate(value) {
    emit('update', {
      field: valueKey,
      value
    })
  }

  function handleInput(e) {
    const value = e.target.value
    localValue.value = value

    if (immediate) {
      emitUpdate(value)
      return
    }

    if (debounceTimer) {
      clearTimeout(debounceTimer)
    }
    debounceTimer = setTimeout(() => {
      emitUpdate(localValue.value)
    }, DEFAULTS.TIMING.DEBOUNCE_DELAY)
  }

  function handleChange(e) {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    localValue.value = value
    emitUpdate(value)
  }

  function handleFocus() {
    isFocused.value = true
    emit('focus')
  }

  function handleBlur() {
    isFocused.value = false
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
    emitUpdate(localValue.value)
    emit('blur')
  }

  function cleanup() {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
  }

  onUnmounted(cleanup)

  return {
    localValue,
    isFocused,
    handleInput,
    handleChange,
    handleFocus,
    handleBlur,
    emitUpdate,
    cleanup
  }
}

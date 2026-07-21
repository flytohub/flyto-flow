/**
 * Element Picker composable — dropdown open/close/direction logic
 * Manages the picker's open state, keyboard navigation focus index,
 * and automatic drop direction based on viewport space.
 */
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'

export function useElementPicker() {
  const containerRef = ref(null)
  const dropdownRef = ref(null)
  const inputRef = ref(null)
  const isOpen = ref(false)
  const focusedIndex = ref(-1)
  const dropDirection = ref('drop-down')

  function toggle(hasSuggestions) {
    if (!hasSuggestions) return
    isOpen.value ? close() : open(hasSuggestions)
  }

  function open(hasSuggestions) {
    if (!hasSuggestions) return
    isOpen.value = true
    focusedIndex.value = -1
    nextTick(updateDropDirection)
  }

  function close() {
    isOpen.value = false
    focusedIndex.value = -1
  }

  function updateDropDirection() {
    if (!containerRef.value) return
    const rect = containerRef.value.getBoundingClientRect()
    const spaceBelow = window.innerHeight - rect.bottom
    dropDirection.value = spaceBelow < 200 ? 'drop-up' : 'drop-down'
  }

  function onClickOutside(e) {
    if (containerRef.value && !containerRef.value.contains(e.target)) {
      close()
    }
  }

  watch(isOpen, (val) => {
    if (val) {
      document.addEventListener('click', onClickOutside, true)
    } else {
      document.removeEventListener('click', onClickOutside, true)
    }
  })

  onBeforeUnmount(() => {
    document.removeEventListener('click', onClickOutside, true)
  })

  return {
    containerRef,
    dropdownRef,
    inputRef,
    isOpen,
    focusedIndex,
    dropDirection,
    toggle,
    open,
    close,
    updateDropDirection,
  }
}

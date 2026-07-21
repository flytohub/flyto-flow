import { ref } from 'vue'
import { localStore } from '@/services/storageService'

// Always use dark mode
document.documentElement.classList.add('dark')
localStore.set('theme', 'dark')

const isDark = ref(true)

export function useDarkMode() {
  const toggle = () => {
    // Disabled - always dark mode
  }

  const setDark = () => {
    // Disabled - always dark mode
  }

  return {
    isDark,
    toggle,
    setDark
  }
}

import { ref, isRef, watch, onUnmounted } from 'vue'
import { DEFAULTS } from '@/config/defaults'

export function useTypingEffect(texts, options = {}) {
  const {
    typeSpeed = DEFAULTS.TIMING.TYPE_SPEED,
    deleteSpeed = 50,
    pauseDuration = DEFAULTS.TIMING.TYPING_INDICATOR
  } = options

  const displayText = ref('')
  let currentTexts = isRef(texts) ? texts.value : texts
  let textIndex = 0
  let charIndex = 0
  let isDeleting = false
  let timeoutId = null

  if (isRef(texts)) {
    watch(texts, (newTexts) => {
      currentTexts = newTexts
      textIndex = 0
      charIndex = 0
      isDeleting = false
    })
  }

  function type() {
    if (!currentTexts || currentTexts.length === 0) return

    const current = currentTexts[textIndex % currentTexts.length]

    if (isDeleting) {
      displayText.value = current.substring(0, charIndex - 1)
      charIndex--
    } else {
      displayText.value = current.substring(0, charIndex + 1)
      charIndex++
    }

    if (!isDeleting && charIndex === current.length) {
      timeoutId = setTimeout(() => {
        isDeleting = true
        type()
      }, pauseDuration)
      return
    } else if (isDeleting && charIndex === 0) {
      isDeleting = false
      textIndex = (textIndex + 1) % currentTexts.length
    }

    const speed = isDeleting ? deleteSpeed : typeSpeed
    timeoutId = setTimeout(type, speed)
  }

  function start() {
    type()
  }

  function stop() {
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutId = null
    }
  }

  onUnmounted(stop)

  return {
    displayText,
    start,
    stop
  }
}

import { onUnmounted } from 'vue'

export function useScrollAnimation(options = {}) {
  const { threshold = 0.1 } = options

  let observers = []

  function observe(elements, callback) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          callback(entry.target)
          observer.unobserve(entry.target)
        }
      })
    }, { threshold })

    if (Array.isArray(elements)) {
      elements.forEach(el => {
        if (el) observer.observe(el)
      })
    } else if (elements) {
      observer.observe(elements)
    }

    observers.push(observer)
    return observer
  }

  function animateIn(element) {
    element.classList.remove('opacity-0', 'translate-y-8', 'scale-90')
    element.classList.add('opacity-100', 'translate-y-0', 'scale-100')
  }

  function animateNumber(element, start, end, duration = 2000) {
    const range = end - start
    const startTime = performance.now()

    function update() {
      const now = performance.now()
      const progress = Math.min((now - startTime) / duration, 1)
      const easeProgress = 1 - Math.pow(1 - progress, 3)
      const current = Math.floor(start + range * easeProgress)

      element.textContent = current.toLocaleString()

      if (progress < 1) {
        requestAnimationFrame(update)
      }
    }

    requestAnimationFrame(update)
  }

  function observeWithCounter(element, targetNumber) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateNumber(entry.target, 0, targetNumber)
          observer.disconnect()
        }
      })
    }, { threshold: 0.5 })

    if (element) {
      observer.observe(element)
      observers.push(observer)
    }

    return observer
  }

  function cleanup() {
    observers.forEach(obs => obs.disconnect())
    observers = []
  }

  onUnmounted(cleanup)

  return {
    observe,
    animateIn,
    animateNumber,
    observeWithCounter,
    cleanup
  }
}

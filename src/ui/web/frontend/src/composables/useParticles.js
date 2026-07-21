import { onUnmounted } from 'vue'
import { DEFAULTS } from '@/config/defaults'

const STAR_COLORS = [
  { r: 139, g: 92, b: 246 },
  { r: 99, g: 102, b: 241 },
  { r: 168, g: 85, b: 247 },
  { r: 236, g: 72, b: 153 },
  { r: 255, g: 255, b: 255 },
  { r: 96, g: 165, b: 250 },
  { r: 244, g: 114, b: 182 },
  { r: 129, g: 140, b: 248 }
]

const CONNECTION_DIST_SQ = 100 * 100

export function useParticles(options = {}) {
  const { starCount = 50, boundaryPercent = 0.45, targetFPS = 30 } = options
  const frameInterval = 1000 / targetFPS

  let animationId = null
  let resizeHandler = null
  let shootingIntervalId = null

  function init(canvas) {
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    const stars = []
    const shootingStars = []

    function resizeCanvas() {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resizeCanvas()

    const getLeftBound = () => canvas.width * boundaryPercent

    class Star {
      constructor() {
        this.reset()
      }

      reset() {
        this.x = Math.random() * getLeftBound()
        this.y = Math.random() * canvas.height
        this.size = Math.random() * 3 + 0.8
        this.baseSize = this.size
        this.color = STAR_COLORS[Math.floor(Math.random() * STAR_COLORS.length)]
        this.twinkleSpeed = Math.random() * 0.03 + 0.008
        this.twinklePhase = Math.random() * Math.PI * 2
        this.vx = (Math.random() - 0.5) * 0.2
        this.vy = (Math.random() - 0.5) * 0.2
        this.glowSize = this.size * (2.5 + Math.random() * 2.5)
      }

      update() {
        this.x += this.vx
        this.y += this.vy

        const leftBound = getLeftBound()
        if (this.x < -10) this.x = leftBound
        if (this.x > leftBound + 10) this.x = 0
        if (this.y < -10) this.y = canvas.height + 10
        if (this.y > canvas.height + 10) this.y = -10

        this.twinklePhase += this.twinkleSpeed
        const twinkle = Math.sin(this.twinklePhase) * 0.5 + 0.5
        this.size = this.baseSize * (0.5 + twinkle * 0.7)
      }

      draw() {
        const twinkle = Math.sin(this.twinklePhase) * 0.5 + 0.5
        const alpha = 0.5 + twinkle * 0.5

        const gradient = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, this.glowSize)
        gradient.addColorStop(0, `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, ${alpha * 0.5})`)
        gradient.addColorStop(0.4, `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, ${alpha * 0.15})`)
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)')

        ctx.fillStyle = gradient
        ctx.beginPath()
        ctx.arc(this.x, this.y, this.glowSize, 0, Math.PI * 2)
        ctx.fill()

        ctx.fillStyle = `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, ${alpha})`
        ctx.beginPath()
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
        ctx.fill()

        ctx.fillStyle = `rgba(255, 255, 255, ${alpha * 0.9})`
        ctx.beginPath()
        ctx.arc(this.x, this.y, this.size * 0.5, 0, Math.PI * 2)
        ctx.fill()
      }
    }

    class ShootingStar {
      constructor() {
        this.reset()
      }

      reset() {
        this.x = Math.random() * canvas.width
        this.y = Math.random() * canvas.height * 0.5
        this.speed = Math.random() * 8 + 6
        this.angle = Math.PI / 4 + (Math.random() - 0.5) * 0.3
        this.opacity = 1
        this.active = false
        this.trail = []
      }

      activate() {
        this.active = true
        this.x = Math.random() * canvas.width * 0.3
        this.y = Math.random() * canvas.height * 0.3
        this.opacity = 1
        this.trail = []
      }

      update() {
        if (!this.active) return

        this.trail.unshift({ x: this.x, y: this.y, opacity: this.opacity })
        if (this.trail.length > 20) this.trail.pop()

        this.x += Math.cos(this.angle) * this.speed
        this.y += Math.sin(this.angle) * this.speed
        this.opacity -= 0.02

        if (this.opacity <= 0 || this.x > canvas.width || this.y > canvas.height) {
          this.active = false
          this.trail = []
        }
      }

      draw() {
        if (!this.active) return

        this.trail.forEach((point, i) => {
          const trailOpacity = point.opacity * (1 - i / this.trail.length) * 0.6
          const trailSize = 2 * (1 - i / this.trail.length)

          ctx.fillStyle = `rgba(255, 255, 255, ${trailOpacity})`
          ctx.beginPath()
          ctx.arc(point.x, point.y, trailSize, 0, Math.PI * 2)
          ctx.fill()
        })

        const gradient = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, 4)
        gradient.addColorStop(0, `rgba(255, 255, 255, ${this.opacity})`)
        gradient.addColorStop(1, 'rgba(139, 92, 246, 0)')

        ctx.fillStyle = gradient
        ctx.beginPath()
        ctx.arc(this.x, this.y, 4, 0, Math.PI * 2)
        ctx.fill()
      }
    }

    for (let i = 0; i < starCount; i++) {
      stars.push(new Star())
    }

    for (let i = 0; i < 3; i++) {
      shootingStars.push(new ShootingStar())
    }

    shootingIntervalId = setInterval(() => {
      const inactive = shootingStars.find(s => !s.active)
      if (inactive && Math.random() < 0.3) {
        inactive.activate()
      }
    }, DEFAULTS.TIMING.PARTICLE_INTERVAL)

    let lastFrameTime = 0

    function animate(timestamp) {
      animationId = requestAnimationFrame(animate)
      if (timestamp - lastFrameTime < frameInterval) return
      lastFrameTime = timestamp

      ctx.clearRect(0, 0, canvas.width, canvas.height)

      stars.forEach(star => {
        star.update()
        star.draw()
      })

      stars.forEach((s1, i) => {
        for (let j = i + 1; j < stars.length; j++) {
          const s2 = stars[j]
          const dx = s1.x - s2.x
          const dy = s1.y - s2.y
          const distSq = dx * dx + dy * dy

          if (distSq < CONNECTION_DIST_SQ) {
            const alpha = 0.08 * (1 - Math.sqrt(distSq) / 100)
            ctx.strokeStyle = `rgba(139, 92, 246, ${alpha})`
            ctx.lineWidth = 0.5
            ctx.beginPath()
            ctx.moveTo(s1.x, s1.y)
            ctx.lineTo(s2.x, s2.y)
            ctx.stroke()
          }
        }
      })

      shootingStars.forEach(star => {
        star.update()
        star.draw()
      })
    }

    animationId = requestAnimationFrame(animate)

    resizeHandler = resizeCanvas
    window.addEventListener('resize', resizeHandler)
  }

  function destroy() {
    if (shootingIntervalId) {
      clearInterval(shootingIntervalId)
      shootingIntervalId = null
    }
    if (animationId) {
      cancelAnimationFrame(animationId)
      animationId = null
    }
    if (resizeHandler) {
      window.removeEventListener('resize', resizeHandler)
      resizeHandler = null
    }
  }

  onUnmounted(destroy)

  return { init, destroy }
}

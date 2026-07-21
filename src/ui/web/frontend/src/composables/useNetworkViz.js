import { onUnmounted } from 'vue'

const ICON_PATHS = {
  play: 'M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z',
  globe: 'M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20M2 12h20M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20',
  pointer: 'M9.037 9.69a.498.498 0 0 1 .653-.653l11 4.5a.5.5 0 0 1-.074.949l-4.349 1.041a1 1 0 0 0-.74.739l-1.04 4.35a.5.5 0 0 1-.95.074z',
  upload: 'M12 3v12M17 8l-5-5-5 5M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4',
  gitBranch: 'M6 3v12M6 18a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM18 6a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM18 9a9 9 0 0 1-9 9',
  repeat: 'M17 2l4 4-4 4M3 11v-1a4 4 0 0 1 4-4h14M7 22l-4-4 4-4M21 13v1a4 4 0 0 1-4 4H3',
  database: 'M3 5a9 3 0 0 1 18 0M3 5v14a9 3 0 0 0 18 0V5M3 12a9 3 0 0 0 18 0',
  zap: 'M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z',
  link: 'M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71',
  square: 'M3 3h18v18H3z'
}

const FILLED_ICONS = ['play', 'zap', 'pointer']

const DEFAULT_NODES = [
  { id: 'n1', x: 55, y: 70, r: 28, color: '#8b5cf6', icon: 'play' },
  { id: 'n2', x: 165, y: 45, r: 24, color: '#3b82f6', icon: 'globe' },
  { id: 'n3', x: 320, y: 55, r: 18, color: '#06b6d4', icon: 'pointer' },
  { id: 'n4', x: 355, y: 155, r: 22, color: '#10b981', icon: 'upload' },
  { id: 'n5', x: 280, y: 235, r: 32, color: '#f59e0b', icon: 'gitBranch' },
  { id: 'n6', x: 65, y: 195, r: 20, color: '#ec4899', icon: 'repeat' },
  { id: 'n7', x: 175, y: 310, r: 26, color: '#8b5cf6', icon: 'database' },
  { id: 'n8', x: 125, y: 135, r: 16, color: '#6366f1', icon: 'zap' },
  { id: 'n9', x: 240, y: 125, r: 14, color: '#14b8a6', icon: 'link' },
  { id: 'n10', x: 350, y: 325, r: 24, color: '#f43f5e', icon: 'square' }
]

const DEFAULT_CONNECTIONS = [
  { from: 'n1', to: 'n2', curve: 30 },
  { from: 'n1', to: 'n6', curve: -40 },
  { from: 'n1', to: 'n8', curve: 20 },
  { from: 'n2', to: 'n3', curve: -25 },
  { from: 'n2', to: 'n9', curve: 35 },
  { from: 'n3', to: 'n4', curve: 40 },
  { from: 'n3', to: 'n9', curve: -30 },
  { from: 'n4', to: 'n5', curve: -35 },
  { from: 'n4', to: 'n10', curve: 25 },
  { from: 'n5', to: 'n7', curve: 45 },
  { from: 'n5', to: 'n10', curve: -20 },
  { from: 'n6', to: 'n7', curve: 30 },
  { from: 'n6', to: 'n8', curve: -25 },
  { from: 'n8', to: 'n9', curve: 35 },
  { from: 'n8', to: 'n2', curve: -40 },
  { from: 'n9', to: 'n5', curve: 30 },
  { from: 'n7', to: 'n10', curve: -35 },
  { from: 'n10', to: 'n1', curve: 50 }
]

export function useNetworkViz(options = {}) {
  const {
    nodes = DEFAULT_NODES,
    connections = DEFAULT_CONNECTIONS,
    particleCount = 25,
    width = 400,
    height = 380,
    targetFPS = 30
  } = options
  const frameInterval = 1000 / targetFPS
  const nodeMap = Object.fromEntries(nodes.map(n => [n.id, n]))

  let animationId = null
  let canvasEl = null
  let resizeHandler = null

  function init(container) {
    if (!container) return

    const canvas = document.createElement('canvas')
    canvas.style.cssText = 'position: absolute; inset: 0; width: 100%; height: 100%;'
    canvas.width = container.clientWidth || width
    canvas.height = container.clientHeight || height
    container.appendChild(canvas)

    resizeHandler = () => {
      canvas.width = container.clientWidth || width
      canvas.height = container.clientHeight || height
    }
    window.addEventListener('resize', resizeHandler)
    canvasEl = canvas
    const ctx = canvas.getContext('2d')

    const particles = []

    class DataParticle {
      constructor() {
        this.reset()
      }

      reset() {
        this.connIndex = Math.floor(Math.random() * connections.length)
        this.conn = connections[this.connIndex]
        this.progress = Math.random()
        this.speed = 0.008 + Math.random() * 0.012
        this.size = 3 + Math.random() * 4
        this.from = nodeMap[this.conn.from]
        this.to = nodeMap[this.conn.to]
        this.color = this.from.color
      }

      update() {
        this.progress += this.speed
        if (this.progress >= 1) {
          this.reset()
          this.progress = 0
        }
      }

      getPosition() {
        const curve = this.conn.curve || 0
        const midX = (this.from.x + this.to.x) / 2
        const midY = (this.from.y + this.to.y) / 2
        const dx = this.to.x - this.from.x
        const dy = this.to.y - this.from.y
        const len = Math.sqrt(dx * dx + dy * dy)
        const nx = -dy / len
        const ny = dx / len
        const ctrlX = midX + nx * curve
        const ctrlY = midY + ny * curve
        const t = this.progress
        const x = (1 - t) * (1 - t) * this.from.x + 2 * (1 - t) * t * ctrlX + t * t * this.to.x
        const y = (1 - t) * (1 - t) * this.from.y + 2 * (1 - t) * t * ctrlY + t * t * this.to.y
        return { x, y }
      }

      draw() {
        const pos = this.getPosition()
        const gradient = ctx.createRadialGradient(pos.x, pos.y, 0, pos.x, pos.y, this.size * 3)
        gradient.addColorStop(0, this.color)
        gradient.addColorStop(0.4, this.color + '80')
        gradient.addColorStop(1, 'transparent')
        ctx.fillStyle = gradient
        ctx.beginPath()
        ctx.arc(pos.x, pos.y, this.size * 3, 0, Math.PI * 2)
        ctx.fill()
        ctx.fillStyle = '#fff'
        ctx.beginPath()
        ctx.arc(pos.x, pos.y, this.size * 0.6, 0, Math.PI * 2)
        ctx.fill()
      }
    }

    for (let i = 0; i < particleCount; i++) {
      particles.push(new DataParticle())
    }

    let time = 0
    let lastFrameTime = 0

    function drawFrame(timestamp) {
      animationId = requestAnimationFrame(drawFrame)
      if (timestamp - lastFrameTime < frameInterval) return
      lastFrameTime = timestamp

      ctx.clearRect(0, 0, canvas.width, canvas.height)
      time += 0.02

      connections.forEach(conn => {
        const from = nodeMap[conn.from]
        const to = nodeMap[conn.to]
        const curve = conn.curve || 0
        const midX = (from.x + to.x) / 2
        const midY = (from.y + to.y) / 2
        const dx = to.x - from.x
        const dy = to.y - from.y
        const len = Math.sqrt(dx * dx + dy * dy)
        const nx = -dy / len
        const ny = dx / len
        const ctrlX = midX + nx * curve
        const ctrlY = midY + ny * curve

        ctx.strokeStyle = 'rgba(139, 92, 246, 0.15)'
        ctx.lineWidth = 6
        ctx.beginPath()
        ctx.moveTo(from.x, from.y)
        ctx.quadraticCurveTo(ctrlX, ctrlY, to.x, to.y)
        ctx.stroke()

        ctx.strokeStyle = 'rgba(139, 92, 246, 0.4)'
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.moveTo(from.x, from.y)
        ctx.quadraticCurveTo(ctrlX, ctrlY, to.x, to.y)
        ctx.stroke()
      })

      particles.forEach(p => {
        p.update()
        p.draw()
      })

      nodes.forEach((node, i) => {
        const pulse = Math.sin(time * 2 + i) * 0.15 + 1

        ctx.strokeStyle = node.color + '40'
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.arc(node.x, node.y, node.r * pulse * 1.3, 0, Math.PI * 2)
        ctx.stroke()

        const glow = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, node.r * 1.5)
        glow.addColorStop(0, node.color + '60')
        glow.addColorStop(1, 'transparent')
        ctx.fillStyle = glow
        ctx.beginPath()
        ctx.arc(node.x, node.y, node.r * 1.5, 0, Math.PI * 2)
        ctx.fill()

        const gradient = ctx.createRadialGradient(node.x - node.r * 0.3, node.y - node.r * 0.3, 0, node.x, node.y, node.r)
        gradient.addColorStop(0, node.color)
        gradient.addColorStop(1, node.color + 'cc')
        ctx.fillStyle = gradient
        ctx.beginPath()
        ctx.arc(node.x, node.y, node.r, 0, Math.PI * 2)
        ctx.fill()

        ctx.strokeStyle = 'rgba(255,255,255,0.3)'
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.arc(node.x, node.y, node.r, 0, Math.PI * 2)
        ctx.stroke()

        const iconSize = node.r * 0.8
        const path = new Path2D(ICON_PATHS[node.icon])
        ctx.save()
        ctx.translate(node.x - iconSize / 2, node.y - iconSize / 2)
        ctx.scale(iconSize / 24, iconSize / 24)
        ctx.lineCap = 'round'
        ctx.lineJoin = 'round'

        if (FILLED_ICONS.includes(node.icon)) {
          ctx.fillStyle = '#fff'
          ctx.fill(path)
        } else {
          ctx.strokeStyle = '#fff'
          ctx.lineWidth = 2
          ctx.stroke(path)
        }
        ctx.restore()
      })

    }

    animationId = requestAnimationFrame(drawFrame)
  }

  function destroy() {
    if (animationId) {
      cancelAnimationFrame(animationId)
      animationId = null
    }
    if (resizeHandler) {
      window.removeEventListener('resize', resizeHandler)
      resizeHandler = null
    }
    if (canvasEl) {
      canvasEl.remove()
      canvasEl = null
    }
  }

  onUnmounted(destroy)

  return { init, destroy }
}

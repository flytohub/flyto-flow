<template>
  <Teleport to="body">
    <Transition name="update-overlay">
      <div v-if="visible" class="update-overlay" @click.stop>
        <!-- Grid background -->
        <div class="update-grid"></div>

        <!-- Aurora bands -->
        <div class="update-aurora">
          <div class="update-aurora-band"></div>
          <div class="update-aurora-band"></div>
          <div class="update-aurora-band"></div>
        </div>

        <!-- Particle canvas -->
        <canvas ref="particleCanvas" class="update-particles"></canvas>

        <!-- Hex grid -->
        <canvas ref="hexCanvas" class="update-hex"></canvas>

        <!-- Ambient glow -->
        <div class="update-ambient"></div>

        <!-- Scan line -->
        <div class="update-scanline"></div>

        <!-- Content -->
        <div class="update-content">
          <!-- Logo with orbits -->
          <div class="update-logo-wrap">
            <div class="update-logo-glow" :class="{ 'glow-intense': phase === 'ready' }"></div>
            <div class="update-orbit-ring"></div>
            <div class="update-orbit-ring-2"></div>
            <div class="update-orbit-ring-3" v-if="phase === 'ready'"></div>
            <div class="update-logo-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 16v-4m0 0V8m0 4h4m-4 0H8" v-if="phase === 'downloading'" />
                <path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" v-else />
              </svg>
            </div>
          </div>

          <!-- Status text with glitch effect -->
          <div class="update-status" :class="{ 'glitch': phase === 'ready' }">
            <span class="update-status-text" :data-text="statusText">{{ statusText }}</span>
          </div>

          <!-- Progress section -->
          <div class="update-progress-section">
            <!-- Progress bar -->
            <div class="update-progress-track">
              <div class="update-progress-bar" :style="{ width: progressPercent + '%' }"></div>
              <div class="update-progress-glow" :style="{ left: progressPercent + '%' }"></div>
            </div>

            <!-- Progress details -->
            <div class="update-progress-info">
              <span class="update-progress-label">{{ progressLabel }}</span>
              <span class="update-progress-pct">{{ Math.round(progressPercent) }}%</span>
            </div>
          </div>

          <!-- Countdown (only during ready phase) -->
          <div v-if="phase === 'ready'" class="update-countdown">
            <div class="update-countdown-ring">
              <svg viewBox="0 0 80 80">
                <circle cx="40" cy="40" r="36" fill="none" stroke="rgba(99,102,241,0.15)" stroke-width="2" />
                <circle cx="40" cy="40" r="36" fill="none" stroke="url(#countdownGrad)" stroke-width="2.5"
                  stroke-linecap="round" :stroke-dasharray="226" :stroke-dashoffset="226 * (1 - countdownProgress)"
                  transform="rotate(-90 40 40)" />
                <defs>
                  <linearGradient id="countdownGrad" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stop-color="#7c3aed" />
                    <stop offset="100%" stop-color="#6366f1" />
                  </linearGradient>
                </defs>
              </svg>
              <span class="update-countdown-num">{{ countdownSeconds }}</span>
            </div>
          </div>

          <!-- Version info -->
          <div class="update-version" v-if="newVersion">
            <span class="update-version-badge">v{{ newVersion }}</span>
          </div>
        </div>

        <!-- Corner decorations -->
        <div class="update-corner update-corner-tl"></div>
        <div class="update-corner update-corner-tr"></div>
        <div class="update-corner update-corner-bl"></div>
        <div class="update-corner update-corner-br"></div>

        <!-- Data stream lines -->
        <div class="update-streams">
          <div class="update-stream" v-for="i in 6" :key="i" :style="streamStyle(i)"></div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'

const visible = ref(false)
const phase = ref('downloading') // 'downloading' | 'ready'
const downloadProgress = ref(0)
const newVersion = ref('')
const countdownSeconds = ref(5)
const countdownProgress = ref(0)

const particleCanvas = ref(null)
const hexCanvas = ref(null)

let animFrameId = null
let hexAnimFrameId = null
let countdownInterval = null
let unlisteners = []

const statusText = computed(() => {
  if (phase.value === 'downloading') return 'UPDATING SYSTEM'
  return 'RESTARTING'
})

const progressPercent = computed(() => {
  if (phase.value === 'downloading') return downloadProgress.value
  return 100
})

const progressLabel = computed(() => {
  if (phase.value === 'downloading') return 'Downloading update...'
  return 'Update installed'
})

function streamStyle(i) {
  const positions = [8, 20, 35, 55, 72, 90]
  const delays = [0, 1.2, 0.6, 1.8, 0.3, 1.5]
  const durations = [2.5, 3, 2.8, 3.2, 2.6, 2.9]
  return {
    left: positions[i - 1] + '%',
    animationDelay: delays[i - 1] + 's',
    animationDuration: durations[i - 1] + 's'
  }
}

// Particle system
function initParticles() {
  const canvas = particleCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  let W, H
  const PARTICLE_COUNT = 80
  const CONNECTION_DIST = 100
  const particles = []

  function resize() {
    W = canvas.width = window.innerWidth
    H = canvas.height = window.innerHeight
  }
  resize()
  window.addEventListener('resize', resize)

  class Particle {
    constructor(init) {
      this.x = Math.random() * W
      this.y = init ? Math.random() * H : H + 4
      this.size = Math.random() * 2.5 + 0.5
      this.vx = (Math.random() - 0.5) * 0.6
      this.vy = -(Math.random() * 0.5 + 0.1)
      this.baseOpacity = Math.random() * 0.5 + 0.15
      this.pulse = Math.random() * Math.PI * 2
      this.hue = 240 + Math.random() * 40
    }
    update() {
      this.x += this.vx
      this.y += this.vy
      this.pulse += 0.02
      this.opacity = this.baseOpacity * (0.5 + 0.5 * Math.sin(this.pulse))
      if (this.x < -10) this.x = W + 10
      if (this.x > W + 10) this.x = -10
      if (this.y < -10) { this.x = Math.random() * W; this.y = H + 10 }
    }
    draw() {
      ctx.beginPath()
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
      ctx.fillStyle = `hsla(${this.hue}, 70%, 72%, ${this.opacity})`
      ctx.fill()
    }
  }

  for (let i = 0; i < PARTICLE_COUNT; i++) particles.push(new Particle(true))

  function animate() {
    ctx.clearRect(0, 0, W, H)
    particles.forEach(p => p.update())
    // Draw connections
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x
        const dy = particles[i].y - particles[j].y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < CONNECTION_DIST) {
          const alpha = (1 - dist / CONNECTION_DIST) * 0.15 *
            Math.min(particles[i].opacity, particles[j].opacity) * 3
          ctx.beginPath()
          ctx.moveTo(particles[i].x, particles[i].y)
          ctx.lineTo(particles[j].x, particles[j].y)
          ctx.strokeStyle = `rgba(139, 92, 246, ${alpha})`
          ctx.lineWidth = 0.6
          ctx.stroke()
        }
      }
    }
    particles.forEach(p => p.draw())
    animFrameId = requestAnimationFrame(animate)
  }
  animate()
}

// Hex grid overlay
function initHexGrid() {
  const canvas = hexCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  let W, H

  function resize() {
    W = canvas.width = window.innerWidth
    H = canvas.height = window.innerHeight
  }
  resize()

  let time = 0
  function animate() {
    ctx.clearRect(0, 0, W, H)
    time += 0.005
    const hexSize = 30
    const rows = Math.ceil(H / (hexSize * 1.5)) + 1
    const cols = Math.ceil(W / (hexSize * Math.sqrt(3))) + 1

    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        const x = col * hexSize * Math.sqrt(3) + (row % 2 ? hexSize * Math.sqrt(3) / 2 : 0)
        const y = row * hexSize * 1.5
        const dist = Math.sqrt((x - W / 2) ** 2 + (y - H / 2) ** 2)
        const maxDist = Math.sqrt((W / 2) ** 2 + (H / 2) ** 2)
        const wave = Math.sin(dist * 0.01 - time * 3) * 0.5 + 0.5
        const fade = 1 - (dist / maxDist)
        const alpha = wave * fade * 0.04

        if (alpha < 0.005) continue
        ctx.beginPath()
        for (let i = 0; i < 6; i++) {
          const angle = Math.PI / 3 * i - Math.PI / 6
          const px = x + hexSize * 0.4 * Math.cos(angle)
          const py = y + hexSize * 0.4 * Math.sin(angle)
          if (i === 0) ctx.moveTo(px, py)
          else ctx.lineTo(px, py)
        }
        ctx.closePath()
        ctx.strokeStyle = `rgba(99, 102, 241, ${alpha})`
        ctx.lineWidth = 0.5
        ctx.stroke()
      }
    }
    hexAnimFrameId = requestAnimationFrame(animate)
  }
  animate()
}

function startCountdown() {
  countdownSeconds.value = 5
  countdownProgress.value = 0
  const startTime = Date.now()
  const duration = 5000

  countdownInterval = setInterval(() => {
    const elapsed = Date.now() - startTime
    countdownProgress.value = Math.min(elapsed / duration, 1)
    countdownSeconds.value = Math.max(0, Math.ceil((duration - elapsed) / 1000))
    if (elapsed >= duration) {
      clearInterval(countdownInterval)
    }
  }, 50)
}

async function setupTauriListeners() {
  // Check if running in Tauri
  if (!window.__TAURI__) return

  try {
    const { listen } = window.__TAURI__.event

    const unlisten1 = await listen('update-downloading', () => {
      visible.value = true
      phase.value = 'downloading'
      downloadProgress.value = 0
    })
    unlisteners.push(unlisten1)

    const unlisten2 = await listen('update-progress', (event) => {
      visible.value = true
      phase.value = 'downloading'
      const pct = event.payload?.progress ?? event.payload ?? 0
      downloadProgress.value = typeof pct === 'number' ? pct : 0
    })
    unlisteners.push(unlisten2)

    const unlisten3 = await listen('update-ready', (event) => {
      phase.value = 'ready'
      downloadProgress.value = 100
      newVersion.value = event.payload?.version || ''
      startCountdown()
    })
    unlisteners.push(unlisten3)
  } catch (e) {
  }
}

watch(visible, async (val) => {
  if (val) {
    await nextTick()
    initParticles()
    initHexGrid()
  } else {
    if (animFrameId) cancelAnimationFrame(animFrameId)
    if (hexAnimFrameId) cancelAnimationFrame(hexAnimFrameId)
  }
})

onMounted(() => {
  setupTauriListeners()
})

onUnmounted(() => {
  unlisteners.forEach(fn => fn())
  if (animFrameId) cancelAnimationFrame(animFrameId)
  if (hexAnimFrameId) cancelAnimationFrame(hexAnimFrameId)
  if (countdownInterval) clearInterval(countdownInterval)
})
</script>

<style scoped>
.update-overlay {
  position: fixed;
  inset: 0;
  z-index: 99999;
  background: #0a0e1a;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  -webkit-user-select: none;
  user-select: none;
}

/* === Grid background === */
.update-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(99,102,241,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(99,102,241,0.04) 1px, transparent 1px);
  background-size: 50px 50px;
  mask-image: radial-gradient(ellipse 80% 70% at 50% 50%, black 20%, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse 80% 70% at 50% 50%, black 20%, transparent 70%);
  animation: gridDrift 15s linear infinite;
}

@keyframes gridDrift {
  0% { transform: translate(0, 0); }
  100% { transform: translate(50px, 50px); }
}

/* === Aurora === */
.update-aurora {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.update-aurora-band {
  position: absolute;
  width: 150%;
  height: 250px;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0;
  animation: auroraDrift linear infinite;
}

.update-aurora-band:nth-child(1) {
  background: linear-gradient(90deg, transparent, rgba(124,58,237,0.18), rgba(99,102,241,0.12), transparent);
  top: 10%;
  left: -25%;
  animation-duration: 14s;
}

.update-aurora-band:nth-child(2) {
  background: linear-gradient(90deg, transparent, rgba(59,130,246,0.12), rgba(139,92,246,0.15), transparent);
  top: 50%;
  left: -25%;
  animation-duration: 18s;
  animation-delay: -5s;
}

.update-aurora-band:nth-child(3) {
  background: linear-gradient(90deg, transparent, rgba(168,85,247,0.1), rgba(99,102,241,0.08), transparent);
  top: 75%;
  left: -25%;
  animation-duration: 12s;
  animation-delay: -8s;
}

@keyframes auroraDrift {
  0% { transform: translateX(-30%) scaleY(1); opacity: 0; }
  15% { opacity: 1; }
  50% { transform: translateX(10%) scaleY(1.4); opacity: 0.9; }
  85% { opacity: 1; }
  100% { transform: translateX(50%) scaleY(1); opacity: 0; }
}

/* === Particles === */
.update-particles {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

/* === Hex grid === */
.update-hex {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  pointer-events: none;
}

/* === Ambient glow === */
.update-ambient {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 600px;
  height: 600px;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(99,102,241,0.08) 0%, rgba(124,58,237,0.04) 40%, transparent 70%);
  animation: ambientPulse 3s ease-in-out infinite;
  pointer-events: none;
  z-index: 2;
}

@keyframes ambientPulse {
  0%, 100% { opacity: 0.6; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.2); }
}

/* === Scan line === */
.update-scanline {
  position: absolute;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(99,102,241,0.3), rgba(139,92,246,0.5), rgba(99,102,241,0.3), transparent);
  box-shadow: 0 0 20px rgba(99,102,241,0.3), 0 0 60px rgba(139,92,246,0.1);
  animation: scanMove 4s ease-in-out infinite;
  z-index: 5;
}

@keyframes scanMove {
  0% { top: -2px; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}

/* === Content === */
.update-content {
  position: relative;
  z-index: 10;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
}

/* === Logo === */
.update-logo-wrap {
  position: relative;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.update-logo-icon {
  width: 48px;
  height: 48px;
  color: #a78bfa;
  position: relative;
  z-index: 5;
  animation: logoFloat 3s ease-in-out infinite;
}

@keyframes logoFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

.update-logo-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 160px;
  height: 160px;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(124,58,237,0.4) 0%, rgba(99,102,241,0.15) 50%, transparent 70%);
  border-radius: 50%;
  filter: blur(12px);
  animation: glowPulse 3s ease-in-out infinite;
  z-index: 1;
}

.update-logo-glow.glow-intense {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(124,58,237,0.6) 0%, rgba(99,102,241,0.25) 50%, transparent 70%);
  animation: glowPulseIntense 1.5s ease-in-out infinite;
}

@keyframes glowPulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.6; }
  50% { transform: translate(-50%, -50%) scale(1.3); opacity: 1; }
}

@keyframes glowPulseIntense {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.7; }
  50% { transform: translate(-50%, -50%) scale(1.5); opacity: 1; }
}

.update-orbit-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100px;
  height: 100px;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 1.5px solid transparent;
  border-top-color: rgba(139, 92, 246, 0.7);
  border-right-color: rgba(99, 102, 241, 0.15);
  z-index: 3;
  animation: orbitSpin 2.5s linear infinite;
}

.update-orbit-ring::after {
  content: '';
  position: absolute;
  top: -3px;
  left: 50%;
  width: 6px;
  height: 6px;
  background: #a78bfa;
  border-radius: 50%;
  box-shadow: 0 0 10px 3px rgba(167, 139, 250, 0.9);
}

.update-orbit-ring-2 {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 130px;
  height: 130px;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 1px solid transparent;
  border-bottom-color: rgba(59, 130, 246, 0.4);
  border-left-color: rgba(99, 102, 241, 0.08);
  z-index: 3;
  animation: orbitSpin 4s linear infinite reverse;
}

.update-orbit-ring-2::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 50%;
  width: 4px;
  height: 4px;
  background: #818cf8;
  border-radius: 50%;
  box-shadow: 0 0 8px 2px rgba(129, 140, 248, 0.7);
}

.update-orbit-ring-3 {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 155px;
  height: 155px;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  border: 1px solid transparent;
  border-top-color: rgba(168, 85, 247, 0.3);
  border-right-color: rgba(139, 92, 246, 0.1);
  z-index: 3;
  animation: orbitSpin 6s linear infinite;
}

.update-orbit-ring-3::after {
  content: '';
  position: absolute;
  top: -2px;
  right: 20%;
  width: 3px;
  height: 3px;
  background: #c084fc;
  border-radius: 50%;
  box-shadow: 0 0 6px 2px rgba(192, 132, 252, 0.6);
}

@keyframes orbitSpin {
  to { transform: translate(-50%, -50%) rotate(360deg); }
}

/* === Status text === */
.update-status {
  position: relative;
}

.update-status-text {
  font-size: 1.1rem;
  font-weight: 600;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  color: #c4b5fd;
  text-shadow: 0 0 20px rgba(139, 92, 246, 0.5);
}

/* Glitch effect */
.update-status.glitch .update-status-text {
  animation: glitchText 2s infinite;
}

.update-status.glitch .update-status-text::before,
.update-status.glitch .update-status-text::after {
  content: attr(data-text);
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
}

.update-status.glitch .update-status-text::before {
  color: #818cf8;
  animation: glitchBefore 2s infinite;
  clip-path: polygon(0 0, 100% 0, 100% 45%, 0 45%);
}

.update-status.glitch .update-status-text::after {
  color: #a78bfa;
  animation: glitchAfter 2s infinite;
  clip-path: polygon(0 55%, 100% 55%, 100% 100%, 0 100%);
}

@keyframes glitchText {
  0%, 90%, 100% { transform: none; }
  92% { transform: skew(-2deg); }
  94% { transform: skew(1deg); }
  96% { transform: skew(-1deg); }
  98% { transform: none; }
}

@keyframes glitchBefore {
  0%, 90%, 100% { transform: none; }
  92% { transform: translateX(-3px); }
  94% { transform: translateX(2px); }
  96% { transform: translateX(-1px); }
}

@keyframes glitchAfter {
  0%, 90%, 100% { transform: none; }
  92% { transform: translateX(3px); }
  94% { transform: translateX(-2px); }
  96% { transform: translateX(1px); }
}

/* === Progress === */
.update-progress-section {
  width: 280px;
}

.update-progress-track {
  height: 3px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 4px;
  overflow: visible;
  position: relative;
  margin-bottom: 0.8rem;
}

.update-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #7c3aed, #6366f1, #818cf8);
  border-radius: 4px;
  box-shadow: 0 0 15px rgba(99, 102, 241, 0.5);
  transition: width 0.5s ease-out;
  position: relative;
}

.update-progress-glow {
  position: absolute;
  top: -4px;
  width: 10px;
  height: 10px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.8), transparent);
  border-radius: 50%;
  transform: translateX(-50%);
  transition: left 0.5s ease-out;
  pointer-events: none;
}

.update-progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.update-progress-label {
  font-size: 0.72rem;
  color: #64748b;
  letter-spacing: 0.04em;
}

.update-progress-pct {
  font-size: 0.72rem;
  color: #818cf8;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

/* === Countdown === */
.update-countdown {
  margin-top: 0.5rem;
}

.update-countdown-ring {
  position: relative;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.update-countdown-ring svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.update-countdown-ring circle {
  transition: stroke-dashoffset 0.05s linear;
}

.update-countdown-num {
  font-size: 1.8rem;
  font-weight: 700;
  color: #c4b5fd;
  text-shadow: 0 0 15px rgba(139, 92, 246, 0.5);
  font-variant-numeric: tabular-nums;
  z-index: 1;
}

/* === Version badge === */
.update-version-badge {
  display: inline-block;
  font-size: 0.7rem;
  color: rgba(139, 92, 246, 0.7);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 999px;
  padding: 0.2rem 0.8rem;
  letter-spacing: 0.06em;
  backdrop-filter: blur(4px);
}

/* === Corner decorations === */
.update-corner {
  position: absolute;
  width: 40px;
  height: 40px;
  z-index: 10;
}

.update-corner::before,
.update-corner::after {
  content: '';
  position: absolute;
  background: rgba(99, 102, 241, 0.3);
}

.update-corner-tl { top: 20px; left: 20px; }
.update-corner-tl::before { top: 0; left: 0; width: 20px; height: 1px; }
.update-corner-tl::after { top: 0; left: 0; width: 1px; height: 20px; }

.update-corner-tr { top: 20px; right: 20px; }
.update-corner-tr::before { top: 0; right: 0; width: 20px; height: 1px; }
.update-corner-tr::after { top: 0; right: 0; width: 1px; height: 20px; }

.update-corner-bl { bottom: 20px; left: 20px; }
.update-corner-bl::before { bottom: 0; left: 0; width: 20px; height: 1px; }
.update-corner-bl::after { bottom: 0; left: 0; width: 1px; height: 20px; }

.update-corner-br { bottom: 20px; right: 20px; }
.update-corner-br::before { bottom: 0; right: 0; width: 20px; height: 1px; }
.update-corner-br::after { bottom: 0; right: 0; width: 1px; height: 20px; }

/* === Data streams === */
.update-streams {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 3;
  overflow: hidden;
}

.update-stream {
  position: absolute;
  top: -100px;
  width: 1px;
  height: 80px;
  background: linear-gradient(to bottom, transparent, rgba(99, 102, 241, 0.15), transparent);
  animation: streamFall linear infinite;
}

@keyframes streamFall {
  0% { top: -100px; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { top: calc(100% + 100px); opacity: 0; }
}

/* === Transition === */
.update-overlay-enter-active {
  transition: opacity 0.6s ease-out;
}

.update-overlay-leave-active {
  transition: opacity 0.3s ease-in;
}

.update-overlay-enter-from,
.update-overlay-leave-to {
  opacity: 0;
}
</style>

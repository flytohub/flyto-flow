<template>
  <div class="background-effects">
    <div class="gradient-orb orb-1"></div>
    <div class="gradient-orb orb-2"></div>
    <div class="gradient-orb orb-3"></div>
    <div class="grid-overlay"></div>
    <div class="particles">
      <div
        v-for="i in particleCount"
        :key="i"
        class="particle"
        :style="getParticleStyle(i)"
      ></div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  particleCount: {
    type: Number,
    default: 20
  }
})

function getParticleStyle(index) {
  const size = 2 + Math.random() * 4
  const duration = 15 + Math.random() * 20
  const delay = Math.random() * 10
  const startX = Math.random() * 100
  const startY = Math.random() * 100

  return {
    width: `${size}px`,
    height: `${size}px`,
    left: `${startX}%`,
    top: `${startY}%`,
    animationDuration: `${duration}s`,
    animationDelay: `${delay}s`,
    opacity: 0.3 + Math.random() * 0.5
  }
}
</script>

<style scoped>
.background-effects {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  top: -200px;
  left: -100px;
  animation-delay: 0s;
}

.orb-2 {
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
  bottom: -150px;
  right: -100px;
  animation-delay: -7s;
}

.orb-3 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #06b6d4 0%, #6366f1 100%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -14s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(30px, -30px) scale(1.05); }
  50% { transform: translate(-20px, 20px) scale(0.95); }
  75% { transform: translate(20px, 10px) scale(1.02); }
}

.grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
  background-size: 50px 50px;
}

.particles {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.particle {
  position: absolute;
  background: linear-gradient(135deg, #a855f7, #6366f1);
  border-radius: 50%;
  animation: floatParticle linear infinite;
}

@keyframes floatParticle {
  0% {
    transform: translateY(0) translateX(0) scale(1);
    opacity: 0;
  }
  10% {
    opacity: 0.6;
  }
  90% {
    opacity: 0.6;
  }
  100% {
    transform: translateY(-100vh) translateX(50px) scale(0.5);
    opacity: 0;
  }
}

</style>

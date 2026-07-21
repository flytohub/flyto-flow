<template>
  <div class="logo-wrapper">
    <div class="logo-glow"></div>
    <div class="logo-rings">
      <div class="ring ring-1"></div>
      <div class="ring ring-2"></div>
      <div class="ring ring-3"></div>
    </div>
    <div class="logo-container">
      <img :src="src" :alt="alt" class="logo-image" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  src: {
    type: String,
    default: '/logo.png'
  },
  alt: {
    type: String,
    default: 'Logo'
  }
})
</script>

<style scoped>
.logo-wrapper {
  position: relative;
  width: 120px;
  height: 120px;
  margin-bottom: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-glow {
  position: absolute;
  inset: -25px;
  background: radial-gradient(circle, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.8) 50%, transparent 100%);
  border-radius: 50%;
  opacity: 1;
  filter: blur(15px);
  animation: logoGlow 4s ease-in-out infinite;
}

.logo-glow::after {
  content: '';
  position: absolute;
  inset: -10px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, rgba(6, 182, 212, 0.5), rgba(59, 130, 246, 0.3), rgba(16, 185, 129, 0.4), rgba(6, 182, 212, 0.5));
  filter: blur(20px);
  opacity: 0.6;
  animation: glowRotate 8s linear infinite;
}

@keyframes logoGlow {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

@keyframes glowRotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.logo-rings {
  position: absolute;
  width: 140px;
  height: 140px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
}

.ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border: 2px solid transparent;
  border-radius: 50%;
}

.ring-1 {
  width: 130px;
  height: 130px;
  border-top-color: rgba(6, 182, 212, 0.7);
  border-right-color: rgba(6, 182, 212, 0.3);
  animation: rotateRing 8s linear infinite;
}

.ring-2 {
  width: 110px;
  height: 110px;
  border-bottom-color: rgba(59, 130, 246, 0.6);
  border-left-color: rgba(59, 130, 246, 0.3);
  animation: rotateRing 6s linear infinite reverse;
}

.ring-3 {
  width: 150px;
  height: 150px;
  border-top-color: rgba(16, 185, 129, 0.4);
  border-left-color: rgba(16, 185, 129, 0.2);
  animation: rotateRing 12s linear infinite;
}

@keyframes rotateRing {
  from { transform: translate(-50%, -50%) rotate(0deg); }
  to { transform: translate(-50%, -50%) rotate(360deg); }
}

.logo-container {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: logoFloat 6s ease-in-out infinite;
  z-index: 2;
}

.logo-container img {
  width: 80px;
  height: 80px;
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
  animation: logoPulse 3s ease-in-out infinite;
}

@keyframes logoFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

@keyframes logoPulse {
  0%, 100% {
    filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3)) brightness(1);
  }
  50% {
    filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.4)) brightness(1.1);
  }
}

@media (max-width: 768px) {
  .logo-wrapper {
    margin: 0 auto 1.5rem;
    width: 100px;
    height: 100px;
  }

  .logo-container img {
    width: 60px;
    height: 60px;
  }

  .ring-1 {
    width: 100px;
    height: 100px;
  }

  .ring-2 {
    width: 85px;
    height: 85px;
  }

  .ring-3 {
    width: 115px;
    height: 115px;
  }

  .logo-rings {
    width: 120px;
    height: 120px;
  }
}

</style>

<template>
  <div class="wave-divider">
    <svg class="wave-svg" viewBox="0 0 1440 140" preserveAspectRatio="none">
      <defs>
        <linearGradient :id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style="stop-color:#8b5cf6;stop-opacity:0.3" />
          <stop offset="50%" style="stop-color:#6366f1;stop-opacity:0.2" />
          <stop offset="100%" style="stop-color:#8b5cf6;stop-opacity:0.3" />
        </linearGradient>
        <linearGradient :id="grad2" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style="stop-color:#06b6d4;stop-opacity:0.2" />
          <stop offset="50%" style="stop-color:#8b5cf6;stop-opacity:0.15" />
          <stop offset="100%" style="stop-color:#06b6d4;stop-opacity:0.2" />
        </linearGradient>
        <filter :id="glowId">
          <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>

      <path class="fill-gray-50 dark:fill-gray-800" d="M0,80 C240,120 480,40 720,80 C960,120 1200,40 1440,80 L1440,140 L0,140 Z"/>

      <path :fill="grad1Url" d="M0,90 C180,130 360,50 540,90 C720,130 900,50 1080,90 C1260,130 1440,50 1440,90 L1440,140 L0,140 Z">
        <animate attributeName="d" dur="8s" repeatCount="indefinite" values="
          M0,90 C180,130 360,50 540,90 C720,130 900,50 1080,90 C1260,130 1440,50 1440,90 L1440,140 L0,140 Z;
          M0,90 C180,50 360,130 540,90 C720,50 900,130 1080,90 C1260,50 1440,130 1440,90 L1440,140 L0,140 Z;
          M0,90 C180,130 360,50 540,90 C720,130 900,50 1080,90 C1260,130 1440,50 1440,90 L1440,140 L0,140 Z
        "/>
      </path>

      <path :fill="grad2Url" d="M0,100 C200,60 400,140 600,100 C800,60 1000,140 1200,100 C1400,60 1440,100 1440,100 L1440,140 L0,140 Z">
        <animate attributeName="d" dur="6s" repeatCount="indefinite" values="
          M0,100 C200,60 400,140 600,100 C800,60 1000,140 1200,100 C1400,60 1440,100 1440,100 L1440,140 L0,140 Z;
          M0,100 C200,140 400,60 600,100 C800,140 1000,60 1200,100 C1400,140 1440,100 1440,100 L1440,140 L0,140 Z;
          M0,100 C200,60 400,140 600,100 C800,60 1000,140 1200,100 C1400,60 1440,100 1440,100 L1440,140 L0,140 Z
        "/>
      </path>

      <g :stroke="grad1Url" stroke-width="1" fill="none" :filter="glowUrl" opacity="0.6">
        <path d="M0,110 Q360,90 720,110 T1440,110">
          <animate attributeName="d" dur="10s" repeatCount="indefinite" values="
            M0,110 Q360,90 720,110 T1440,110;
            M0,110 Q360,130 720,110 T1440,110;
            M0,110 Q360,90 720,110 T1440,110
          "/>
        </path>
        <path d="M0,120 Q480,100 960,120 T1440,120">
          <animate attributeName="d" dur="12s" repeatCount="indefinite" values="
            M0,120 Q480,100 960,120 T1440,120;
            M0,120 Q480,140 960,120 T1440,120;
            M0,120 Q480,100 960,120 T1440,120
          "/>
        </path>
      </g>

      <g fill="#8b5cf6" :filter="glowUrl">
        <circle r="3" opacity="0.8">
          <animate attributeName="cx" dur="8s" repeatCount="indefinite" values="0;1440"/>
          <animate attributeName="cy" dur="8s" repeatCount="indefinite" values="110;100;120;110"/>
        </circle>
        <circle r="2" opacity="0.6">
          <animate attributeName="cx" dur="6s" repeatCount="indefinite" values="200;1640"/>
          <animate attributeName="cy" dur="6s" repeatCount="indefinite" values="115;105;125;115"/>
        </circle>
        <circle r="2.5" opacity="0.7">
          <animate attributeName="cx" dur="10s" repeatCount="indefinite" values="500;1940"/>
          <animate attributeName="cy" dur="10s" repeatCount="indefinite" values="108;98;118;108"/>
        </circle>
      </g>
    </svg>
  </div>
</template>

<script setup>
import { getCurrentInstance } from 'vue'

const uid = `wave-${getCurrentInstance()?.uid ?? 0}`
const grad1 = `wg1-${uid}`
const grad2 = `wg2-${uid}`
const glowId = `glow-${uid}`
const grad1Url = `url(#${grad1})`
const grad2Url = `url(#${grad2})`
const glowUrl = `url(#${glowId})`
</script>

<style scoped>
.wave-divider {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  overflow: hidden;
}

.wave-svg {
  position: relative;
  display: block;
  width: 100%;
  height: 6rem;
}

@media (min-width: 640px) {
  .wave-svg {
    height: 8rem;
  }
}

@media (min-width: 1024px) {
  .wave-svg {
    height: 10rem;
  }
}
</style>

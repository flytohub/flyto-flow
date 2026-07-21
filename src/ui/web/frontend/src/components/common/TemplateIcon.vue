<template>
  <div
    class="template-icon"
    :class="[sizeClass, { 'is-dark': isDark, 'is-transparent': transparent }]"
    :style="customColorStyle"
  >
    <!-- Animated gradient border -->
    <div class="icon-border">
      <div class="border-glow"></div>
    </div>

    <!-- Inner content -->
    <div class="icon-inner">
      <img
        v-if="iconUrl"
        :src="iconUrl"
        :alt="alt"
        loading="lazy"
        decoding="async"
        class="icon-image"
      />
      <component
        v-else
        :is="resolvedIcon"
        :size="iconSize"
        class="icon-fallback"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, inject } from 'vue'
import {
  Zap, Globe, Database, Bell, Brain, Terminal, ShoppingCart, Share2, Folder
} from 'lucide-vue-next'

const props = defineProps({
  iconUrl: { type: String, default: '' },
  category: { type: String, default: 'other' },
  size: { type: String, default: 'md' },
  alt: { type: String, default: 'Icon' },
  transparent: { type: Boolean, default: false },
  color: { type: String, default: '' }
})

// Check dark mode from document
const isDark = computed(() => {
  if (typeof document !== 'undefined') {
    return document.documentElement.classList.contains('dark')
  }
  return true
})

const categoryIcons = {
  automation: Zap,
  browser: Globe,
  data: Database,
  notification: Bell,
  ai: Brain,
  devops: Terminal,
  ecommerce: ShoppingCart,
  social: Share2,
  other: Folder
}

const sizes = {
  sm: { class: 'size-sm', icon: 18 },
  md: { class: 'size-md', icon: 22 },
  lg: { class: 'size-lg', icon: 28 },
  xl: { class: 'size-xl', icon: 40 }
}

const resolvedIcon = computed(() => categoryIcons[props.category] || Folder)
const sizeClass = computed(() => sizes[props.size]?.class || 'size-md')
const iconSize = computed(() => sizes[props.size]?.icon || 22)

// Adjust color brightness helper
function adjustColor(hex, amount) {
  if (!hex) return '#8B5CF6'
  let color = hex.replace('#', '')
  if (color.length === 3) {
    color = color.split('').map(c => c + c).join('')
  }
  const num = parseInt(color, 16)
  const r = Math.min(255, Math.max(0, (num >> 16) + amount))
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0x00ff) + amount))
  const b = Math.min(255, Math.max(0, (num & 0x0000ff) + amount))
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`
}

// Custom color support
const customColorStyle = computed(() => {
  if (!props.color) return {}
  const darkerColor = adjustColor(props.color, -60)
  const darkestColor = adjustColor(props.color, -100)
  return {
    '--icon-color': props.color,
    '--icon-color-light': props.color + '40',
    '--icon-color-glow': props.color + '60',
    '--icon-bg-start': darkerColor,
    '--icon-bg-end': darkestColor
  }
})
</script>

<style scoped>
.template-icon {
  position: relative;
  flex-shrink: 0;
}

.size-sm { width: 36px; height: 36px; }
.size-md { width: 44px; height: 44px; }
.size-lg { width: 56px; height: 56px; }
.size-xl { width: 80px; height: 80px; }

/* Animated border container */
.icon-border {
  position: absolute;
  inset: 0;
  border-radius: 12px;
  padding: 1.5px;
  background: linear-gradient(135deg, var(--icon-color, #6366f1), var(--icon-color, #8b5cf6), var(--icon-color-light, #ec4899), var(--icon-color, #6366f1));
  background-size: 300% 300%;
  animation: borderGlow 3s ease infinite;
  opacity: 0.8;
}

.size-sm .icon-border { border-radius: 10px; padding: 1px; }
.size-xl .icon-border { border-radius: 16px; padding: 2px; }

/* Glow effect */
.border-glow {
  position: absolute;
  inset: -2px;
  border-radius: inherit;
  background: linear-gradient(135deg, var(--icon-color, #6366f1), var(--icon-color, #8b5cf6), var(--icon-color-light, #ec4899), var(--icon-color, #6366f1));
  background-size: 300% 300%;
  animation: borderGlow 3s ease infinite;
  filter: blur(6px);
  opacity: 0.4;
  z-index: -1;
}

.template-icon:hover .border-glow {
  opacity: 0.7;
  filter: blur(8px);
}

.template-icon:hover .icon-border {
  opacity: 1;
}

/* Inner icon area - uses custom color or dark fallback */
.icon-inner {
  position: absolute;
  inset: 1.5px;
  border-radius: 11px;
  background: linear-gradient(145deg, var(--icon-bg-start, #1f2937), var(--icon-bg-end, #111827));
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  /* Fix WebKit webview: overflow:hidden + border-radius doesn't clip images */
  -webkit-mask-image: -webkit-radial-gradient(white, black);
  isolation: isolate;
}

.size-sm .icon-inner { inset: 1px; border-radius: 9px; }
.size-xl .icon-inner { inset: 2px; border-radius: 14px; }

/* Icon image */
.icon-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: inherit;
  filter: drop-shadow(0 0 4px var(--icon-color-glow, rgba(139, 92, 246, 0.3)));
}

/* Fallback icon - dark mode */
.icon-fallback {
  color: rgba(255, 255, 255, 0.85);
  filter: drop-shadow(0 0 4px rgba(139, 92, 246, 0.4));
}

/* Transparent mode - no background, no border */
.is-transparent .icon-border,
.is-transparent .border-glow {
  display: none;
}

.is-transparent .icon-inner {
  background: transparent;
  inset: 0;
}

.is-transparent .icon-image {
  width: 100%;
  height: 100%;
  filter: none;
}

/* Gradient animation */
@keyframes borderGlow {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
</style>

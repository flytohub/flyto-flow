<template>
  <div class="tab-bar">
    <!-- Tabs -->
    <div class="tabs">
      <button
        @click="$emit('update:activeTab', 'ui')"
        :class="['tab', { active: activeTab === 'ui' }]"
      >
        <div class="tab-icon-wrap">
          <Palette :size="18" />
        </div>
        <div class="tab-label">
          <span class="label-main">{{ $t('templateBuilder.tabs.uiDesign') }}</span>
          <span class="label-sub">INTERFACE</span>
        </div>
        <div class="tab-active-bar"></div>
      </button>

      <button
        @click="$emit('update:activeTab', 'workflow')"
        :class="['tab', { active: activeTab === 'workflow' }]"
      >
        <div class="tab-icon-wrap">
          <Code :size="18" />
        </div>
        <div class="tab-label">
          <span class="label-main">{{ $t('templateBuilder.tabs.backendWorkflow') }}</span>
          <span class="label-sub">BACKEND</span>
        </div>
        <div class="tab-active-bar"></div>
      </button>

    </div>

    <!-- AI Chat button removed — now global via FloatingChatButton in App.vue -->
  </div>
</template>

<script setup>
import { Palette, Code } from 'lucide-vue-next'

defineProps({
  activeTab: {
    type: String,
    required: true
  }
})

defineEmits(['update:activeTab'])
</script>

<style scoped>
.tab-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
  background: #070a10;
  position: relative;
  overflow: hidden;
}

/* Tabs */
.tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 1;
}

/* Tab button */
.tab {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

/* Icon wrapper */
.tab-icon-wrap {
  position: relative;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #475569;
  transition: all 0.3s ease;
}

.tab:hover .tab-icon-wrap {
  color: #818cf8;
}

.tab.active .tab-icon-wrap {
  color: #a5b4fc;
}

/* First tab colors */
.tabs .tab:first-child:hover .tab-icon-wrap,
.tabs .tab:first-child.active .tab-icon-wrap {
  color: #f472b6;
}

/* Second tab colors */
.tabs .tab:last-child:hover .tab-icon-wrap,
.tabs .tab:last-child.active .tab-icon-wrap {
  color: #60a5fa;
}

/* Labels */
.tab-label {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.label-main {
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  transition: all 0.3s ease;
}

.label-sub {
  font-size: 9px;
  font-weight: 600;
  color: #334155;
  letter-spacing: 1.5px;
  transition: all 0.3s ease;
}

.tab:hover .label-main {
  color: #94a3b8;
}

.tab:hover .label-sub {
  color: #475569;
}

.tab.active .label-main {
  color: #e2e8f0;
}

.tab.active .label-sub {
  color: #6366f1;
}

/* First tab (pink) - animated colors */
.tabs .tab:first-child.active .label-main {
  background: linear-gradient(90deg, #ec4899, #f472b6, #fb7185, #ec4899);
  background-size: 300% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: color-shift-pink 3s linear infinite;
}

.tabs .tab:first-child.active .label-sub {
  background: linear-gradient(90deg, #ec4899, #f9a8d4, #ec4899);
  background-size: 200% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: color-shift-pink 2s linear infinite;
}

@keyframes color-shift-pink {
  0% { background-position: 0% 50%; }
  100% { background-position: 100% 50%; }
}

/* Second tab (blue) - animated colors */
.tabs .tab:last-child.active .label-main {
  background: linear-gradient(90deg, #3b82f6, #60a5fa, #93c5fd, #3b82f6);
  background-size: 300% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: color-shift-blue 3s linear infinite;
}

.tabs .tab:last-child.active .label-sub {
  background: linear-gradient(90deg, #3b82f6, #93c5fd, #3b82f6);
  background-size: 200% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: color-shift-blue 2s linear infinite;
}

@keyframes color-shift-blue {
  0% { background-position: 0% 50%; }
  100% { background-position: 100% 50%; }
}

/* Active bar with wave effect */
.tab-active-bar {
  position: absolute;
  bottom: 0;
  left: 20%;
  right: 20%;
  height: 2px;
  border-radius: 2px;
  opacity: 0;
  transition: opacity 0.3s ease;
  overflow: visible;
}

.tab-active-bar::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, #6366f1, #a78bfa, #6366f1, transparent);
  background-size: 200% 100%;
  animation: wave-flow 2s linear infinite;
  border-radius: 2px;
}

.tab-active-bar::after {
  content: '';
  position: absolute;
  inset: -2px -4px;
  background: linear-gradient(90deg, transparent, #6366f1, transparent);
  background-size: 200% 100%;
  animation: wave-flow 2s linear infinite;
  filter: blur(4px);
  opacity: 0.6;
}

@keyframes wave-flow {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}

.tab.active .tab-active-bar {
  opacity: 1;
}

.tabs .tab:first-child .tab-active-bar::before {
  background: linear-gradient(90deg, transparent, #ec4899, #f472b6, #ec4899, transparent);
  background-size: 200% 100%;
}

.tabs .tab:first-child .tab-active-bar::after {
  background: linear-gradient(90deg, transparent, #ec4899, transparent);
  background-size: 200% 100%;
}

.tabs .tab:last-child .tab-active-bar::before {
  background: linear-gradient(90deg, transparent, #3b82f6, #60a5fa, #3b82f6, transparent);
  background-size: 200% 100%;
}

.tabs .tab:last-child .tab-active-bar::after {
  background: linear-gradient(90deg, transparent, #3b82f6, transparent);
  background-size: 200% 100%;
}

/* Locked tab styling */
.locked-tab {
  cursor: not-allowed;
  opacity: 0.6;
}

.locked-tab .tab-icon-wrap {
  color: #f59e0b;
}

.locked-tab .label-main {
  color: #f59e0b;
}

.locked-tab .label-sub {
  color: #d97706;
}


</style>

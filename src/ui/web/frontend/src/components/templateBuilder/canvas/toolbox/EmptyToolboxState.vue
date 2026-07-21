<template>
  <div class="empty-toolbox">
    <div class="empty-icon">
      <MousePointerClick :size="32" />
    </div>
    <p class="empty-title">{{ $t('templateBuilder.componentToolbox.selectColumnMessage') }}</p>
    <p class="empty-hint">{{ $t('templateBuilder.componentToolbox.clickToSelect') }}</p>

    <!-- Visual guide -->
    <div class="guide-steps">
      <div class="guide-step">
        <div class="step-number">1</div>
        <span>Add a section</span>
      </div>
      <div class="guide-arrow">
        <ChevronRight :size="16" />
      </div>
      <div class="guide-step">
        <div class="step-number">2</div>
        <span>Select column</span>
      </div>
      <div class="guide-arrow">
        <ChevronRight :size="16" />
      </div>
      <div class="guide-step">
        <div class="step-number">3</div>
        <span>Add components</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { MousePointerClick, ChevronRight } from 'lucide-vue-next'
</script>

<style scoped>
.empty-toolbox {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding: 24px;
}

.empty-icon {
  width: 72px;
  height: 72px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(6, 182, 212, 0.2) 100%);
  border: 1px solid rgba(139, 92, 246, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a78bfa;
  margin-bottom: 20px;
  animation: iconFloat 3s ease-in-out infinite;
}

@keyframes iconFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

.empty-title {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 600;
  color: #e2e8f0;
}

.empty-hint {
  margin: 0 0 24px;
  font-size: 13px;
  color: #94a3b8;
}

.guide-steps {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 14px;
  background: rgba(30, 41, 59, 0.5);
}

.guide-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.step-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #06b6d4);
  color: white;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.guide-step span {
  font-size: 11px;
  color: #94a3b8;
  white-space: nowrap;
}

.guide-arrow {
  color: #475569;
}
</style>

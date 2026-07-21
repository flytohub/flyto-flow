<template>
  <Teleport to="body">
    <button
      v-show="!modelValue"
      class="floating-chat-btn"
      @click="$emit('update:modelValue', true)"
      title="Open AI Chat"
    >
      <div class="btn-bg"></div>
      <div class="btn-icon">
        <MessageCircle :size="22" />
      </div>
      <div class="btn-pulse"></div>
    </button>
  </Teleport>
</template>

<script setup>
import { MessageCircle } from 'lucide-vue-next'

defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.floating-chat-btn {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  z-index: 9999;
  padding: 0;
  overflow: visible;
  transition: transform 0.2s ease;
}

.floating-chat-btn:hover {
  transform: scale(1.08);
}

.floating-chat-btn:active {
  transform: scale(0.95);
}

.btn-bg {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4);
  transition: all 0.2s ease;
}

.floating-chat-btn:hover .btn-bg {
  box-shadow: 0 6px 28px rgba(139, 92, 246, 0.5);
}

.btn-icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: white;
  z-index: 1;
}

.btn-pulse {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid rgba(139, 92, 246, 0.5);
  animation: pulse-ring 2.5s ease-in-out infinite;
  pointer-events: none;
}

@keyframes pulse-ring {
  0% {
    transform: scale(1);
    opacity: 0.7;
  }
  70% {
    transform: scale(1.25);
    opacity: 0;
  }
  100% {
    transform: scale(1.25);
    opacity: 0;
  }
}
</style>

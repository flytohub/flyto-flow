<template>
  <div class="basic-info">
    <div class="prop-group">
      <label class="prop-label">
        <Package :size="14" />
        {{ $t('templateBuilder.nodeProperties.module') }}
      </label>
      <div class="input-with-copy">
        <AppInput
          :modelValue="module"
          disabled
          size="sm"
        />
        <button
          class="copy-btn"
          :class="{ copied: copiedField === 'module' }"
          @click="copy(module)"
          :title="$t('workflow.clipboard.copied', 'Copy')"
        >
          <Check v-if="copiedField === 'module'" :size="13" />
          <Copy v-else :size="13" />
        </button>
      </div>
    </div>

    <div class="prop-group">
      <label class="prop-label">
        <Hash :size="14" />
        {{ $t('templateBuilder.nodeProperties.nodeId') }}
      </label>
      <div class="input-with-copy">
        <AppInput
          :modelValue="nodeId"
          disabled
          size="sm"
        />
        <button
          class="copy-btn"
          :class="{ copied: copiedField === 'nodeId' }"
          @click="copy(nodeId, 'nodeId')"
          :title="$t('workflow.clipboard.copied', 'Copy')"
        >
          <Check v-if="copiedField === 'nodeId'" :size="13" />
          <Copy v-else :size="13" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Hash, Package, Copy, Check } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'

defineProps({
  nodeId: {
    type: String,
    required: true
  },
  module: {
    type: String,
    required: true
  }
})

const copiedField = ref(null)
let copyTimer = null

function copy(text, field = 'module') {
  navigator.clipboard.writeText(text)
  copiedField.value = field
  clearTimeout(copyTimer)
  copyTimer = setTimeout(() => { copiedField.value = null }, 1500)
}
</script>

<style scoped>
.prop-group {
  margin-bottom: 20px;
}

.prop-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 8px;
}

.input-with-copy {
  position: relative;
  display: flex;
  align-items: center;
}

.prop-input {
  width: 100%;
  padding: 10px 36px 10px 12px;
  border: 1px solid #475569;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.6);
  color: #f1f5f9;
  font-size: 13px;
  transition: all 0.2s;
}

.prop-input.disabled {
  background: rgba(30, 41, 59, 0.5);
  color: #64748b;
  cursor: default;
}

.copy-btn {
  position: absolute;
  right: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: none;
  border-radius: 5px;
  background: transparent;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
}

.copy-btn:hover {
  background: rgba(56, 189, 248, 0.1);
  color: #38bdf8;
  box-shadow: 0 0 8px rgba(56, 189, 248, 0.15);
}

.copy-btn:active {
  transform: scale(0.9);
}

.copy-btn.copied {
  color: #34d399;
  animation: copy-flash 0.4s ease;
}

.copy-btn :deep(svg) {
  flex-shrink: 0;
}

@keyframes copy-flash {
  0% { transform: scale(0.6); opacity: 0.4; }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); opacity: 1; }
}
</style>

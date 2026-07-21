<template>
  <div class="keyvalue-preview">
    <PreviewLabel
      v-if="!hideLabel"
      :label="component.label"
      :required="component.validation?.required"
    />
    <!-- Existing pairs -->
    <div v-for="(pair, index) in pairs" :key="index" class="kv-row">
      <input
        type="text"
        :value="pair.key"
        placeholder="Key"
        :disabled="!editable"
        class="kv-input kv-key"
        @input="updatePair(index, 'key', $event.target.value)"
      />
      <input
        type="text"
        :value="pair.value"
        placeholder="Value"
        :disabled="!editable"
        class="kv-input kv-value"
        @input="updatePair(index, 'value', $event.target.value)"
      />
      <button v-if="editable" class="kv-remove" @click="removePair(index)">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
    <!-- Empty state -->
    <div v-if="pairs.length === 0" class="kv-empty">No items</div>
    <!-- Add button -->
    <button v-if="editable" class="kv-add" @click="addPair">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
      </svg>
      Add
    </button>
    <PreviewHelp :text="component.helpText" />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import PreviewLabel from '@/components/common/PreviewLabel.vue'
import PreviewHelp from '@/components/common/PreviewHelp.vue'

const props = defineProps({
  component: { type: Object, required: true },
  editable: { type: Boolean, default: true },
  hideLabel: { type: Boolean, default: false }
})

const emit = defineEmits(['update', 'focus', 'blur'])

const pairs = ref([])

watch(() => props.component.default, (val) => {
  if (val && typeof val === 'object' && !Array.isArray(val)) {
    pairs.value = Object.entries(val).map(([key, value]) => ({ key, value }))
  }
}, { immediate: true })

function emitPairs() {
  const obj = {}
  for (const p of pairs.value) {
    if (p.key) obj[p.key] = p.value
  }
  emit('update', { field: 'default', value: obj })
}

function addPair() {
  pairs.value.push({ key: '', value: '' })
}

function removePair(index) {
  pairs.value.splice(index, 1)
  emitPairs()
}

function updatePair(index, field, value) {
  pairs.value[index][field] = value
  emitPairs()
}

function focus() {}
defineExpose({ focus })
</script>

<style scoped>
.keyvalue-preview {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.kv-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.kv-input {
  flex: 1;
  min-width: 0;
  padding: 8px 12px;
  border: 1px solid #475569;
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.8);
  color: #f1f5f9;
  font-size: 13px;
  outline: none;
  transition: all 0.2s;
}

.kv-input::placeholder {
  color: #64748b;
}

.kv-input:focus {
  border-color: #8B5CF6;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
}

.kv-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.kv-remove {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
}

.kv-remove:hover {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

.kv-empty {
  padding: 12px;
  text-align: center;
  color: #64748b;
  font-size: 12px;
}

.kv-add {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(139, 92, 246, 0.1);
  border: 1px dashed rgba(139, 92, 246, 0.3);
  border-radius: 6px;
  color: #a78bfa;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.kv-add:hover {
  background: rgba(139, 92, 246, 0.2);
  border-color: rgba(139, 92, 246, 0.5);
}
</style>

<template>
  <div class="key-value-editor">
    <div v-for="(item, index) in items" :key="item.id" class="kv-row">
      <div class="kv-row-header">
        <span class="kv-row-label">{{ keyLabel }}</span>
        <button v-if="!readOnly" class="kv-remove-btn" @click="removeItem(index)" :title="$t('common.remove')">
          <Trash2 :size="13" />
        </button>
      </div>
      <AppInput v-model="item.key" :placeholder="keyPlaceholder" :readonly="readOnly" size="sm" @blur="emitUpdate" />
      <span class="kv-row-label">{{ valueLabel }}</span>
      <ValueSourceSelector
        :modelValue="item.value"
        inputType="text"
        :placeholder="valuePlaceholder"
        :readonly="readOnly"
        :uiInputFields="uiInputFields"
        :previousSteps="previousSteps"
        @update:modelValue="updateValue(index, $event)"
      />
    </div>

    <div v-if="items.length === 0" class="kv-empty">{{ emptyText }}</div>

    <button v-if="!readOnly" class="kv-add-btn" @click="addItem">
      <Plus :size="14" />
      {{ addText }}
    </button>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus, Trash2 } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import ValueSourceSelector from '../../ValueSourceSelector.vue'

const { t } = useI18n()
let nextId = 0
let ignoreUntil = 0

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) },
  keyLabel: { type: String, default: 'Key' },
  valueLabel: { type: String, default: 'Value' },
  keyPlaceholder: { type: String, default: 'Enter key...' },
  valuePlaceholder: { type: String, default: 'Enter value...' },
  addText: { type: String, default: 'Add' },
  emptyText: { type: String, default: 'No items' },
  readOnly: { type: Boolean, default: false },
  uiInputFields: { type: Array, default: () => [] },
  previousSteps: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:modelValue'])
const items = ref([])

function toItems(obj) {
  if (!obj || typeof obj !== 'object') return []
  return Object.entries(obj).map(([key, value]) => ({
    id: nextId++,
    key,
    value: (typeof value === 'object' && value !== null) ? JSON.stringify(value) : String(value)
  }))
}

function emitUpdate() {
  const result = {}
  for (const item of items.value) {
    if (item.key?.trim()) result[item.key.trim()] = item.value
  }
  ignoreUntil = Date.now() + 1000
  emit('update:modelValue', result)
}

// Only sync from parent when NOT from our own round-trip
watch(() => props.modelValue, (val) => {
  if (Date.now() < ignoreUntil) return
  items.value = toItems(val)
}, { immediate: true, deep: true })

function updateValue(index, val) {
  items.value[index].value = val
  emitUpdate()
}

function addItem() {
  items.value.push({ id: nextId++, key: '', value: '' })
}

function removeItem(index) {
  items.value.splice(index, 1)
  emitUpdate()
}
</script>

<style scoped>
.key-value-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kv-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px;
  background: rgba(15, 23, 42, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 8px;
}

.kv-row-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.kv-row-label {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.kv-remove-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.kv-remove-btn:hover {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.kv-empty {
  padding: 16px;
  text-align: center;
  font-size: 12px;
  color: #64748b;
  background: rgba(15, 23, 42, 0.4);
  border: 1px dashed #475569;
  border-radius: 8px;
}

.kv-add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px dashed #475569;
  border-radius: 6px;
  background: transparent;
  color: #94a3b8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.kv-add-btn:hover {
  border-color: #8B5CF6;
  color: #c4b5fd;
  background: rgba(139, 92, 246, 0.1);
}
</style>

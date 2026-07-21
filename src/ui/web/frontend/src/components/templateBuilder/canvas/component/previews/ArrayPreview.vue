<template>
  <div class="array-preview">
    <PreviewLabel
      v-if="!hideLabel"
      :label="component.label"
      :required="component.validation?.required"
    />
    <!-- Tag list -->
    <div v-if="items.length > 0" class="tag-list">
      <span v-for="(item, index) in items" :key="index" class="tag-item">
        <span class="tag-text">{{ item }}</span>
        <button v-if="editable" class="tag-remove" @click="removeItem(index)">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </span>
    </div>
    <!-- Add input -->
    <div v-if="editable" class="tag-input-row">
      <input
        ref="inputRef"
        type="text"
        v-model="newItem"
        :placeholder="component.placeholder || 'Type and press Enter'"
        class="preview-input"
        @keydown.enter.prevent="addItem"
        @focus="handleFocus"
        @blur="handleBlur"
      />
      <button class="add-btn" :disabled="!newItem.trim()" @click="addItem">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
      </button>
    </div>
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

const inputRef = ref(null)
const newItem = ref('')
const items = ref([])

// Sync from component default
watch(() => props.component.default, (val) => {
  if (Array.isArray(val)) items.value = [...val]
}, { immediate: true })

function addItem() {
  const val = newItem.value.trim()
  if (!val) return
  items.value.push(val)
  newItem.value = ''
  emit('update', { field: 'default', value: [...items.value] })
}

function removeItem(index) {
  items.value.splice(index, 1)
  emit('update', { field: 'default', value: [...items.value] })
}

function handleFocus() { emit('focus') }
function handleBlur() { emit('blur') }

function focus() {
  inputRef.value?.focus()
}

defineExpose({ focus })
</script>

<style scoped>
.array-preview {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 6px;
  font-size: 12px;
  color: #c4b5fd;
}

.tag-text {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tag-remove {
  display: flex;
  align-items: center;
  padding: 0;
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  transition: color 0.15s;
}

.tag-remove:hover {
  color: #ef4444;
}

.tag-input-row {
  display: flex;
  gap: 6px;
}

.preview-input {
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

.preview-input::placeholder {
  color: #64748b;
}

.preview-input:focus {
  border-color: #8B5CF6;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
}

.add-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 6px;
  color: #a78bfa;
  cursor: pointer;
  transition: all 0.15s;
}

.add-btn:hover:not(:disabled) {
  background: rgba(139, 92, 246, 0.25);
  border-color: rgba(139, 92, 246, 0.5);
}

.add-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>

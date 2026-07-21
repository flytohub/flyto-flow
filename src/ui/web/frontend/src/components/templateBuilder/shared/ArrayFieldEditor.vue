<template>
  <div class="array-field-editor">
    <!-- Simple array (string items) → tag-like input -->
    <template v-if="isSimpleArray">
      <div class="tag-list" v-if="items.length > 0">
        <span v-for="(item, index) in items" :key="index" class="tag-item">
          <span class="tag-text">{{ item }}</span>
          <button v-if="!readOnly" class="tag-remove" @click="removeItem(index)">
            <X :size="12" />
          </button>
        </span>
      </div>
      <div v-if="!readOnly" class="tag-input-wrapper">
        <AppInput
          v-model="newItemValue"
          :placeholder="placeholder || t('common.addItem', 'Type and press Enter')"
          @keydown.enter.prevent="addSimpleItem"
          size="sm"
        />
        <button class="tag-add-btn" @click="addSimpleItem" :disabled="!newItemValue.trim()">
          <Plus :size="14" />
        </button>
      </div>
    </template>

    <!-- Object array → expandable card list -->
    <template v-else-if="isObjectArray">
      <div v-for="(item, index) in items" :key="item._id" class="array-card">
        <div class="card-header">
          <span class="card-index">#{{ index + 1 }}</span>
          <span class="card-summary">{{ getCardSummary(item, index) }}</span>
          <div class="card-actions">
            <button v-if="!readOnly && index > 0" class="card-btn" @click="moveItem(index, -1)" :title="t('common.moveUp', 'Move up')">
              <ChevronUp :size="14" />
            </button>
            <button v-if="!readOnly && index < items.length - 1" class="card-btn" @click="moveItem(index, 1)" :title="t('common.moveDown', 'Move down')">
              <ChevronDown :size="14" />
            </button>
            <button v-if="!readOnly" class="card-btn card-btn-danger" @click="removeItem(index)" :title="t('common.remove', 'Remove')">
              <Trash2 :size="13" />
            </button>
          </div>
        </div>
        <div class="card-body" v-if="expandedIndex === index || items.length <= 3">
          <div v-for="prop in itemProperties" :key="prop.key" class="card-field">
            <label class="card-field-label">{{ prop.label || prop.key }}</label>
            <!-- Enum/options → combobox: select + manual input toggle -->
            <AppSelect
              v-if="getItemFieldOptions(prop).length > 0"
              :modelValue="item[prop.key]"
              :disabled="readOnly"
              :placeholder="prop.placeholder || t('common.select', 'Select...')"
              :options="getItemFieldOptions(prop).map(opt => ({ value: opt.value, label: opt.label || opt.value }))"
              @update:modelValue="updateItemProp(index, prop.key, $event)"
            />
            <ValueSourceSelector
              v-else
              :modelValue="item[prop.key]"
              :inputType="getItemInputType(prop)"
              :placeholder="prop.placeholder || ''"
              :readonly="readOnly"
              :uiInputFields="uiInputFields"
              :previousSteps="previousSteps"
              @update:modelValue="updateItemProp(index, prop.key, $event)"
            />
          </div>
        </div>
        <button
          v-else
          class="card-expand-btn"
          @click="expandedIndex = index"
        >
          {{ t('common.expand', 'Edit...') }}
        </button>
      </div>

      <div v-if="items.length === 0" class="array-empty">
        {{ t('common.noItems', 'No items') }}
      </div>

      <button v-if="!readOnly && (!field.maxItems || items.length < field.maxItems)" class="array-add-btn" @click="addObjectItem">
        <Plus :size="14" />
        {{ t('common.add', 'Add') }}
      </button>
    </template>

    <!-- Fallback: JSON textarea -->
    <template v-else>
      <AppTextarea
        v-model="jsonValue"
        :rows="4"
        :placeholder="'[\n  \n]'"
        :readonly="readOnly"
        @blur="parseJsonValue"
        size="sm"
      />
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus, X, Trash2, ChevronUp, ChevronDown } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'
import ValueSourceSelector from '../../ValueSourceSelector.vue'

const { t } = useI18n()
let nextId = 0

const props = defineProps({
  field: { type: Object, default: () => ({}) },
  value: { type: Array, default: () => [] },
  readOnly: { type: Boolean, default: false },
  placeholder: { type: String, default: '' },
  uiInputFields: { type: Array, default: () => [] },
  previousSteps: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:value'])

const newItemValue = ref('')
const expandedIndex = ref(null)
const jsonValue = ref('[]')

// Detect array item type
const itemsSchema = computed(() => props.field.items || {})

const isSimpleArray = computed(() => {
  const itemType = itemsSchema.value.type
  return !itemType || itemType === 'string' || itemType === 'number' || itemType === 'integer'
})

const isObjectArray = computed(() => {
  return itemsSchema.value.type === 'object' || !!itemsSchema.value.properties
})

// Get properties of object items
const itemProperties = computed(() => {
  const schema = itemsSchema.value
  if (!schema.properties) return []
  return Object.entries(schema.properties).map(([key, def]) => ({
    key,
    ...def
  }))
})

// Internal items with stable IDs for object arrays
const items = ref([])

function syncFromValue(val) {
  const arr = Array.isArray(val) ? val : []
  if (isObjectArray.value) {
    items.value = arr.map(item => ({
      _id: nextId++,
      ...(typeof item === 'object' && item !== null ? item : {})
    }))
  } else {
    items.value = [...arr]
  }
  try {
    jsonValue.value = JSON.stringify(arr, null, 2)
  } catch { /* ignore */ }
}

syncFromValue(props.value)

watch(() => props.value, (val) => {
  syncFromValue(val)
}, { deep: true })

function emitUpdate() {
  if (isObjectArray.value) {
    const clean = items.value.map(item => {
      const copy = { ...item }
      delete copy._id
      return copy
    })
    emit('update:value', clean)
  } else {
    emit('update:value', [...items.value])
  }
}

// Simple array methods
function addSimpleItem() {
  const val = newItemValue.value.trim()
  if (!val) return
  items.value.push(val)
  newItemValue.value = ''
  emitUpdate()
}

// Object array methods
function addObjectItem() {
  const newItem = { _id: nextId++ }
  for (const prop of itemProperties.value) {
    newItem[prop.key] = prop.default ?? ''
  }
  items.value.push(newItem)
  expandedIndex.value = items.value.length - 1
  emitUpdate()
}

function updateItemProp(index, key, value) {
  items.value[index][key] = value
  emitUpdate()
}

// Shared methods
function removeItem(index) {
  items.value.splice(index, 1)
  emitUpdate()
}

function moveItem(index, direction) {
  const newIndex = index + direction
  if (newIndex < 0 || newIndex >= items.value.length) return
  const temp = items.value[index]
  items.value[index] = items.value[newIndex]
  items.value[newIndex] = temp
  emitUpdate()
}

function getCardSummary(item, index) {
  if (itemProperties.value.length === 0) return ''
  const first = itemProperties.value[0]
  const val = item[first.key]
  if (val && typeof val === 'string' && val.length > 0) {
    return val.length > 40 ? val.slice(0, 40) + '...' : val
  }
  return ''
}

function getItemInputType(prop) {
  if (prop.format === 'multiline') return 'textarea'
  if (prop.format === 'password') return 'password'
  if (prop.format === 'url') return 'url'
  if (prop.format === 'email') return 'email'
  if (prop.format === 'color') return 'color'
  if (prop.format === 'date') return 'date'
  if (prop.format === 'datetime') return 'datetime'
  if (prop.format === 'path') return 'path'
  if (prop.type === 'number' || prop.type === 'integer') return 'number'
  if (prop.type === 'boolean') return 'boolean'
  // enum/options handled separately via getItemFieldOptions
  return 'text'
}

function getItemFieldOptions(prop) {
  if (prop.options && Array.isArray(prop.options) && prop.options.length > 0) {
    return prop.options
  }
  if (prop.enum && Array.isArray(prop.enum) && prop.enum.length > 0) {
    return prop.enum.map(v => ({ value: v, label: v }))
  }
  return []
}

// JSON fallback
function parseJsonValue() {
  try {
    const parsed = JSON.parse(jsonValue.value)
    if (Array.isArray(parsed)) {
      emit('update:value', parsed)
    }
  } catch { /* ignore invalid JSON */ }
}
</script>

<style scoped>
.array-field-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Tag list (simple arrays) */
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
  max-width: 200px;
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

.tag-input-wrapper {
  display: flex;
  gap: 6px;
}

.tag-input {
  flex: 1;
  padding: 8px 12px;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(7, 11, 20, 0.9) 100%);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.tag-input:focus {
  border-color: #8B5CF6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.tag-input::placeholder {
  color: #475569;
}

.tag-add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  color: #a78bfa;
  cursor: pointer;
  transition: all 0.15s;
}

.tag-add-btn:hover:not(:disabled) {
  background: rgba(139, 92, 246, 0.25);
  border-color: rgba(139, 92, 246, 0.5);
}

.tag-add-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Object array cards */
.array-card {
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 8px;
  transition: border-color 0.15s;
}

.array-card:hover {
  border-color: rgba(139, 92, 246, 0.3);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(15, 23, 42, 0.6);
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 8px 8px 0 0;
}

.card-index {
  font-size: 11px;
  font-weight: 600;
  color: #8B5CF6;
  min-width: 24px;
}

.card-summary {
  flex: 1;
  font-size: 12px;
  color: #94a3b8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-actions {
  display: flex;
  gap: 2px;
}

.card-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
}

.card-btn:hover {
  background: rgba(139, 92, 246, 0.15);
  color: #a78bfa;
}

.card-btn-danger:hover {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  background: rgba(15, 23, 42, 0.3);
}

.card-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-field-label {
  font-size: 11px;
  font-weight: 500;
  color: #94a3b8;
}

.card-expand-btn {
  width: 100%;
  padding: 8px;
  background: transparent;
  border: none;
  color: #8B5CF6;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s;
}

.card-expand-btn:hover {
  background: rgba(139, 92, 246, 0.1);
}

/* Shared */
.array-empty {
  padding: 16px;
  text-align: center;
  color: #64748b;
  font-size: 12px;
}

.array-add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(139, 92, 246, 0.1);
  border: 1px dashed rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  color: #a78bfa;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.array-add-btn:hover {
  background: rgba(139, 92, 246, 0.2);
  border-color: rgba(139, 92, 246, 0.5);
}

/* JSON fallback */
.array-json-textarea {
  width: 100%;
  padding: 10px 12px;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(7, 11, 20, 0.9) 100%);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 8px;
  color: #e2e8f0;
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 12px;
  resize: vertical;
  outline: none;
  box-sizing: border-box;
}

.array-json-textarea:focus {
  border-color: #8B5CF6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}
</style>

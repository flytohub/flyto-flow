<template>
  <div class="switch-cases-editor">
    <label class="section-label">
      <GitMerge :size="14" />
      {{ $t('flow.switch.cases') }}
    </label>

    <!-- Cases List -->
    <div class="cases-list">
      <div
        v-for="(caseItem, index) in localCases"
        :key="caseItem.id"
        class="case-item"
        :style="{ '--case-color': getCaseColor(index) }"
      >
        <div class="case-header">
          <div class="case-color-dot" :style="{ background: getCaseColor(index) }"></div>
          <span class="case-number">{{ $t('flow.switch.case') }} {{ index + 1 }}</span>
          <button
            v-if="!readOnly && localCases.length > 1"
            class="delete-case-btn"
            @click="removeCase(index)"
            :title="$t('common.delete')"
          >
            <X :size="14" />
          </button>
        </div>

        <div class="case-fields">
          <div class="case-field">
            <label class="field-label">{{ $t('flow.switch.value') }}</label>
            <AppInput
              v-model="caseItem.value"
              :placeholder="$t('flow.switch.valuePlaceholder')"
              :readonly="readOnly"
              @update:modelValue="emitUpdate"
              size="sm"
            />
          </div>
          <div class="case-field">
            <label class="field-label">{{ $t('flow.switch.label') }}</label>
            <AppInput
              v-model="caseItem.label"
              :placeholder="$t('flow.switch.labelPlaceholder')"
              :readonly="readOnly"
              @update:modelValue="emitUpdate"
              size="sm"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Add Case Button -->
    <button
      v-if="!readOnly"
      class="add-case-btn"
      @click="addCase"
    >
      <Plus :size="16" />
      {{ $t('flow.switch.addCase') }}
    </button>

    <!-- Default Output Info -->
    <div class="default-info">
      <AlertCircle :size="12" />
      <span>{{ $t('flow.switch.defaultInfo') }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { GitMerge, Plus, X, AlertCircle } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  readOnly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const localCases = ref([])

const caseColors = ['#10B981', '#3B82F6', '#F59E0B', '#EC4899', '#8B5CF6', '#06B6D4', '#EF4444', '#84CC16']

function getCaseColor(index) {
  return caseColors[index % caseColors.length]
}

function generateCaseId() {
  return `case_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`
}

function initCases() {
  if (props.modelValue && props.modelValue.length > 0) {
    localCases.value = props.modelValue.map(c => ({
      id: c.id || generateCaseId(),
      value: c.value || '',
      label: c.label || ''
    }))
  } else {
    // Default cases
    localCases.value = [
      { id: generateCaseId(), value: 'case1', label: 'Case 1' },
      { id: generateCaseId(), value: 'case2', label: 'Case 2' }
    ]
    emitUpdate()
  }
}

function addCase() {
  const newIndex = localCases.value.length + 1
  localCases.value.push({
    id: generateCaseId(),
    value: `case${newIndex}`,
    label: `Case ${newIndex}`
  })
  emitUpdate()
}

function removeCase(index) {
  if (localCases.value.length > 1) {
    localCases.value.splice(index, 1)
    emitUpdate()
  }
}

function emitUpdate() {
  emit('update:modelValue', localCases.value.map(c => ({
    id: c.id,
    value: c.value,
    label: c.label
  })))
}

watch(() => props.modelValue, (newVal) => {
  if (JSON.stringify(newVal) !== JSON.stringify(localCases.value)) {
    initCases()
  }
}, { deep: true })

onMounted(() => {
  initCases()
})
</script>

<style scoped>
.switch-cases-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
}

.cases-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.case-item {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid #334155;
  border-left: 3px solid var(--case-color, #8B5CF6);
  border-radius: 8px;
  padding: 12px;
  transition: all 0.2s;
}

.case-item:hover {
  border-color: #475569;
  background: rgba(30, 41, 59, 0.8);
}

.case-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.case-color-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.case-number {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  flex: 1;
}

.delete-case-btn {
  padding: 4px;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.delete-case-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.case-fields {
  display: flex;
  gap: 10px;
}

.case-field {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-label {
  font-size: 10px;
  font-weight: 500;
  color: #64748b;
}

.case-input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #475569;
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.6);
  color: #f1f5f9;
  font-size: 12px;
  transition: all 0.2s;
}

.case-input:focus {
  outline: none;
  border-color: #8B5CF6;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.15);
}

.case-input[readonly] {
  opacity: 0.7;
  cursor: default;
}

.add-case-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  background: rgba(139, 92, 246, 0.1);
  border: 1px dashed #8B5CF6;
  border-radius: 8px;
  color: #a78bfa;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.add-case-btn:hover {
  background: rgba(139, 92, 246, 0.2);
  border-style: solid;
}

.default-info {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(100, 116, 139, 0.1);
  border-radius: 6px;
  font-size: 11px;
  color: #94a3b8;
}
</style>

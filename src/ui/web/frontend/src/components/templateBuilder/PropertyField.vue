<template>
  <div class="prop-group">
    <!-- Label -->
    <label class="prop-label">
      <component :is="icon" :size="14" />
      {{ label }}
      <span v-if="required">*</span>
    </label>

    <!-- Input Row -->
    <div class="prop-row">
      <slot name="input">
        <!-- Default input -->
        <AppInput
          v-if="inputType === 'text'"
          :modelValue="modelValue"
          @update:modelValue="$emit('update:modelValue', $event)"
          :placeholder="placeholder"
          size="sm"
        />
        <input
          v-else-if="inputType === 'number'"
          :value="modelValue"
          @input="$emit('update:modelValue', $event.target.value)"
          type="number"
          :class="['prop-input', { mono: monospace }]"
          :placeholder="placeholder"
        />
        <AppTextarea
          v-else-if="inputType === 'textarea'"
          :modelValue="modelValue"
          @update:modelValue="$emit('update:modelValue', $event)"
          @blur="$emit('blur', $event)"
          :rows="rows"
          :placeholder="placeholder"
          size="sm"
        />
        <AppSelect
          v-else-if="inputType === 'select'"
          :modelValue="modelValue"
          @update:modelValue="$emit('update:modelValue', $event)"
          :options="options"
        />
      </slot>

      <!-- Settings Button -->
      <button
        v-if="expandable"
        @click="toggleExpand"
        class="settings-btn"
        :class="{ active: isExpanded, 'align-top': inputType === 'textarea' }"
        :title="settingsTitle"
      >
        <Settings :size="14" />
      </button>
    </div>

    <!-- Expanded Options Slot -->
    <Transition name="expand">
      <div v-if="expandable && isExpanded" class="expanded-options">
        <slot name="expanded"></slot>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Settings } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  icon: {
    type: [Object, Function],
    required: true
  },
  modelValue: {
    type: [String, Number],
    default: ''
  },
  inputType: {
    type: String,
    default: 'text' // text, number, textarea, select
  },
  placeholder: {
    type: String,
    default: ''
  },
  required: {
    type: Boolean,
    default: false
  },
  expandable: {
    type: Boolean,
    default: false
  },
  expanded: {
    type: Boolean,
    default: false
  },
  monospace: {
    type: Boolean,
    default: false
  },
  rows: {
    type: Number,
    default: 3
  },
  options: {
    type: Array,
    default: () => []
  },
  settingsTitle: {
    type: String,
    default: 'More options'
  }
})

const emit = defineEmits(['update:modelValue', 'update:expanded', 'blur'])

const isExpanded = ref(props.expanded)

function toggleExpand() {
  isExpanded.value = !isExpanded.value
  emit('update:expanded', isExpanded.value)
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

.prop-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.prop-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #475569;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.6);
  color: #f1f5f9;
  font-size: 13px;
  transition: all 0.2s;
}

.prop-input:focus {
  outline: none;
  border-color: #8B5CF6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.prop-input.mono {
  font-family: 'SF Mono', Monaco, monospace;
}

.prop-textarea {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #475569;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.6);
  color: #f1f5f9;
  font-size: 13px;
  font-family: 'SF Mono', Monaco, monospace;
  resize: vertical;
  transition: all 0.2s;
}

.prop-textarea:focus {
  outline: none;
  border-color: #8B5CF6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.settings-btn {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: 1px solid #475569;
  background: rgba(71, 85, 105, 0.2);
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.settings-btn:hover {
  background: rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.3);
  color: #a78bfa;
}

.settings-btn.active {
  background: rgba(139, 92, 246, 0.2);
  border-color: #8B5CF6;
  color: #8B5CF6;
}

.settings-btn.align-top {
  align-self: flex-start;
  margin-top: 2px;
}

.expanded-options {
  margin-top: 12px;
  padding: 14px;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid #334155;
  border-radius: 8px;
}

/* Expand Transition */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease-out;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
  padding: 0 14px;
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 500px;
}
</style>

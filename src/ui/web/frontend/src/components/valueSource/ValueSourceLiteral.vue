<template>
  <template v-if="inputType === 'text'">
    <input
      v-model="model"
      type="text"
      :placeholder="placeholder || t('valueSource.defaultPlaceholder')"
      class="value-input"
      :readonly="readonly"
      @input="$emit('input')"
    />
  </template>
  <NumberInput
    v-else-if="inputType === 'number'"
    v-model="model"
    inputClass="value-input"
    :placeholder="placeholder || t('valueSource.defaultPlaceholder')"
    :readonly="readonly"
    @update:modelValue="$emit('input')"
  />
  <textarea
    v-else-if="inputType === 'textarea'"
    v-model="model"
    :placeholder="placeholder || t('valueSource.defaultPlaceholder')"
    class="value-textarea"
    rows="3"
    :readonly="readonly"
    @input="$emit('input')"
  ></textarea>
  <AppSelect
    v-else-if="inputType === 'boolean'"
    v-model="model"
    :disabled="readonly"
    @change="$emit('input')"
    :options="[
      { value: true, label: t('valueSource.booleanTrue') },
      { value: false, label: t('valueSource.booleanFalse') }
    ]"
  />
  <!-- Password input with toggle -->
  <div v-else-if="inputType === 'password'" class="password-wrapper">
    <input
      :type="showPassword ? 'text' : 'password'"
      v-model="model"
      class="value-input"
      :placeholder="placeholder || t('valueSource.defaultPlaceholder')"
      :readonly="readonly"
      @input="$emit('input')"
    />
    <button v-if="!readonly" type="button" class="toggle-password-btn" @click="showPassword = !showPassword">
      <Eye v-if="!showPassword" :size="14" />
      <EyeOff v-else :size="14" />
    </button>
  </div>
  <!-- URL input -->
  <input
    v-else-if="inputType === 'url'"
    type="url"
    v-model="model"
    class="value-input"
    :placeholder="placeholder || 'https://'"
    :readonly="readonly"
    @input="$emit('input')"
  />
  <!-- Email input -->
  <input
    v-else-if="inputType === 'email'"
    type="email"
    v-model="model"
    class="value-input"
    :placeholder="placeholder || 'user@flyto2.com'"
    :readonly="readonly"
    @input="$emit('input')"
  />
  <!-- Color input -->
  <div v-else-if="inputType === 'color'" class="color-wrapper">
    <input
      type="color"
      v-model="model"
      class="color-swatch"
      :disabled="readonly"
      @input="$emit('input')"
    />
    <input
      type="text"
      v-model="model"
      class="value-input"
      placeholder="#000000"
      :readonly="readonly"
      @input="$emit('input')"
    />
  </div>
  <!-- Date input -->
  <input
    v-else-if="inputType === 'date'"
    type="date"
    v-model="model"
    class="value-input date-input"
    :readonly="readonly"
    @input="$emit('input')"
    @change="$emit('input')"
  />
  <!-- Datetime input -->
  <input
    v-else-if="inputType === 'datetime'"
    type="datetime-local"
    v-model="model"
    class="value-input date-input"
    :readonly="readonly"
    @input="$emit('input')"
    @change="$emit('input')"
  />
  <!-- Path input with native browse -->
  <div v-else-if="inputType === 'path'" class="path-wrapper">
    <button v-if="!readonly" type="button" class="path-browse-btn" :title="t('valueSource.browsePath', 'Browse')" @click="$emit('browse-path')">
      <FolderOpen :size="14" />
    </button>
    <span v-else class="path-icon"><Folder :size="14" /></span>
    <input
      type="text"
      v-model="model"
      class="value-input"
      :placeholder="placeholder || '/path/to/file'"
      :readonly="readonly"
      @input="$emit('input')"
    />
  </div>
  <!-- Fallback: unknown inputType -->
  <input
    v-else
    v-model="model"
    type="text"
    :placeholder="placeholder || t('valueSource.defaultPlaceholder')"
    class="value-input"
    :readonly="readonly"
    @input="$emit('input')"
  />
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Eye, EyeOff, Folder, FolderOpen } from 'lucide-vue-next'
import NumberInput from '@/components/common/NumberInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'

const { t } = useI18n()

const rawModel = defineModel({ default: '' })

// Objects/Arrays must be displayed as JSON string in text inputs
const model = computed({
  get() {
    const v = rawModel.value
    if (v !== null && v !== undefined && typeof v === 'object') {
      return JSON.stringify(v, null, 2)
    }
    return v ?? ''
  },
  set(newVal) {
    // Try to parse JSON back to object if it was originally an object
    if (typeof rawModel.value === 'object' && rawModel.value !== null) {
      try {
        rawModel.value = JSON.parse(newVal)
        return
      } catch {
        // Not valid JSON, store as string
      }
    }
    rawModel.value = newVal
  },
})

defineProps({
  inputType: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  readonly: { type: Boolean, default: false },
})

defineEmits(['input', 'browse-path'])

const showPassword = ref(false)
</script>

<style scoped>
.value-input,
.value-textarea {
  flex: 1;
  min-width: 0;
  padding: 10px 12px;
  background: transparent;
  border: none;
  color: #e2e8f0;
  font-size: 13px;
  outline: none;
}

.value-input::placeholder,
.value-textarea::placeholder {
  color: #475569;
}

.value-input[readonly],
.value-textarea[readonly] {
  cursor: default;
  opacity: 0.8;
}

.value-textarea {
  resize: vertical;
  min-height: 80px;
}

.password-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  min-width: 0;
}

.password-wrapper .value-input {
  flex: 1;
  min-width: 0;
}

.toggle-password-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.toggle-password-btn:hover {
  background: rgba(139, 92, 246, 0.15);
  color: #a78bfa;
}

.color-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.color-swatch {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  padding: 2px;
  margin-left: 8px;
  background: transparent;
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 6px;
  cursor: pointer;
}

.color-swatch::-webkit-color-swatch-wrapper {
  padding: 0;
}

.color-swatch::-webkit-color-swatch {
  border: none;
  border-radius: 4px;
}

.color-wrapper .value-input {
  flex: 1;
  min-width: 0;
}

.date-input {
  color-scheme: dark;
}

.path-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  min-width: 0;
}

.path-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding-left: 10px;
  color: #64748b;
}

.path-browse-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  margin-left: 4px;
  background: rgba(139, 92, 246, 0.1);
  border: none;
  border-radius: 6px;
  color: #a78bfa;
  cursor: pointer;
  transition: all 0.2s;
}

.path-browse-btn:hover {
  background: rgba(139, 92, 246, 0.25);
  color: #c4b5fd;
}

.path-wrapper .value-input {
  flex: 1;
  min-width: 0;
  padding-left: 6px;
}
</style>

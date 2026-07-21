<template>
  <div class="param-container">
    <div class="param-field">
      <label class="param-label">{{ $t('templateBuilder.nodeProperties.variableName') }}</label>
      <AppInput v-model="params.variableName" placeholder="variable_name" :readonly="readOnly" size="sm" />
      <small class="param-hint">
        {{ $t('templateBuilder.nodeProperties.referenceAs') }}
        <code class="code-tag">{{ params.variableName }}</code>
      </small>
    </div>

    <div class="param-field">
      <label class="param-label">{{ $t('templateBuilder.nodeProperties.label') }}</label>
      <AppInput v-model="params.label" :placeholder="$t('templateBuilder.nodeProperties.label')" :readonly="readOnly" size="sm" />
    </div>

    <div v-if="params.placeholder !== undefined" class="param-field">
      <label class="param-label">{{ $t('templateBuilder.nodeProperties.placeholder') }}</label>
      <AppInput v-model="params.placeholder" :placeholder="$t('templateBuilder.nodeProperties.placeholder')" :readonly="readOnly" size="sm" />
    </div>

    <div v-if="params.required !== undefined" class="param-checkbox">
      <input type="checkbox" v-model="params.required" id="node-form-required" class="cyber-checkbox" :class="{ readonly: readOnly }" @click="readOnly && $event.preventDefault()" />
      <label for="node-form-required" class="checkbox-label">{{ $t('templateBuilder.nodeProperties.requiredField') }}</label>
    </div>

    <!-- Number input specific -->
    <template v-if="moduleType === 'form.input_number'">
      <div class="param-field">
        <label class="param-label">{{ $t('templateBuilder.nodeProperties.minimumValue') }}</label>
        <NumberInput v-model="params.min" inputClass="prop-input" :placeholder="$t('templateBuilder.nodeProperties.noMinimum')" :readonly="readOnly" />
      </div>
      <div class="param-field">
        <label class="param-label">{{ $t('templateBuilder.nodeProperties.maximumValue') }}</label>
        <NumberInput v-model="params.max" inputClass="prop-input" :placeholder="$t('templateBuilder.nodeProperties.noMaximum')" :readonly="readOnly" />
      </div>
    </template>

    <!-- Select input specific -->
    <div v-if="moduleType === 'form.input_select'" class="param-field">
      <label class="param-label">{{ $t('templateBuilder.nodeProperties.optionsPerLine') }}</label>
      <AppTextarea
        :modelValue="Array.isArray(params.options) ? params.options.join('\n') : ''"
        @update:modelValue="params.options = $event.split('\n').filter(o => o.trim())"
        :rows="4"
        :placeholder="$t('templateBuilder.nodeProperties.optionsPlaceholder')"
        :readonly="readOnly"
        size="sm"
      />
    </div>

    <!-- File upload specific -->
    <template v-if="moduleType === 'form.input_file'">
      <div class="param-field">
        <label class="param-label">{{ $t('templateBuilder.nodeProperties.acceptedFileTypes') }}</label>
        <AppInput v-model="params.accept" placeholder="* (all files)" :readonly="readOnly" size="sm" />
        <small class="param-hint">{{ $t('templateBuilder.nodeProperties.fileTypesHint') }}</small>
      </div>
      <div class="param-checkbox">
        <input type="checkbox" v-model="params.multiple" id="node-form-multiple" class="cyber-checkbox" :class="{ readonly: readOnly }" @click="readOnly && $event.preventDefault()" />
        <label for="node-form-multiple" class="checkbox-label">{{ $t('templateBuilder.nodeProperties.allowMultipleFiles') }}</label>
      </div>
    </template>

    <div class="param-field">
      <label class="param-label">{{ $t('templateBuilder.nodeProperties.defaultValue') }}</label>
      <div v-if="moduleType === 'form.input_color'" class="color-default-row">
        <input
          type="color"
          :value="params.default || '#000000'"
          class="color-swatch"
          :disabled="readOnly"
          @input="params.default = $event.target.value"
        />
        <AppInput v-model="params.default" placeholder="#000000" :readonly="readOnly" size="sm" />
      </div>
      <AppInput v-else v-model="params.default" :placeholder="$t('templateBuilder.nodeProperties.defaultValue')" :readonly="readOnly" size="sm" />
    </div>
  </div>
</template>

<script setup>
import AppInput from '@/components/common/AppInput.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'
import NumberInput from '@/components/common/NumberInput.vue'

defineProps({
  params: {
    type: Object,
    required: true
  },
  moduleType: {
    type: String,
    required: true
  },
  readOnly: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.param-container {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 14px;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid #334155;
  border-radius: 8px;
}

.param-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.param-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
}

.param-hint {
  font-size: 10px;
  color: #475569;
}

.param-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cyber-checkbox {
  width: 16px;
  height: 16px;
  accent-color: #8B5CF6;
}

.cyber-checkbox.readonly {
  cursor: default;
  opacity: 0.8;
}

.checkbox-label {
  font-size: 12px;
  color: #94a3b8;
}

.prop-input {
  width: 100%;
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

.prop-input[readonly] {
  cursor: default;
  opacity: 0.8;
}

.code-tag {
  padding: 2px 6px;
  background: rgba(139, 92, 246, 0.2);
  border-radius: 4px;
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 11px;
  color: #A78BFA;
}

.color-default-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-swatch {
  width: 34px;
  height: 34px;
  padding: 2px;
  border: 1px solid #475569;
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.6);
  cursor: pointer;
  flex-shrink: 0;
}

.color-swatch::-webkit-color-swatch-wrapper {
  padding: 0;
}

.color-swatch::-webkit-color-swatch {
  border: none;
  border-radius: 4px;
}
</style>

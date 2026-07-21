<template>
  <div class="nested-object-editor">
    <div v-for="prop in properties" :key="prop.key" class="nested-field">
      <label class="nested-field-label">
        {{ prop.label || prop.key }}
        <span v-if="prop.required" class="nested-required">*</span>
      </label>
      <p v-if="prop.description" class="nested-field-desc">{{ prop.description }}</p>
      <SchemaField
        :field="prop"
        :value="(modelValue || {})[prop.key] ?? prop.default ?? ''"
        :readonly="readOnly"
        :uiInputFields="uiInputFields"
        :previousSteps="previousSteps"
        :allParams="modelValue || {}"
        @update:value="updateProp(prop.key, $event)"
      />
    </div>

    <div v-if="properties.length === 0" class="nested-empty">
      No properties defined
    </div>
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent } from 'vue'
import { formatLabel } from '@/composables/paramRenderer'

// Lazy import to break circular dependency (SchemaField imports NestedObjectEditor)
const SchemaField = defineAsyncComponent(() =>
  import('../SchemaField.vue')
)

const props = defineProps({
  field: { type: Object, required: true },
  modelValue: { type: Object, default: () => ({}) },
  readOnly: { type: Boolean, default: false },
  uiInputFields: { type: Array, default: () => [] },
  previousSteps: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:modelValue'])

const properties = computed(() => {
  const schema = props.field.properties || {}
  const required = props.field.required || []
  return Object.entries(schema).map(([key, def]) => ({
    ...def,
    key,
    label: def.label || formatLabel(key),
    description: def.description || '',
    type: def.type || 'string',
    required: required.includes(key) || def.required === true,
    default: def.default,
  }))
})

function updateProp(key, value) {
  const updated = { ...(props.modelValue || {}), [key]: value }
  emit('update:modelValue', updated)
}
</script>

<style scoped>
.nested-object-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
  background: rgba(15, 23, 42, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 8px;
}

.nested-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nested-field-label {
  font-size: 12px;
  font-weight: 500;
  color: #94a3b8;
}

.nested-required {
  color: #f87171;
  margin-left: 2px;
}

.nested-field-desc {
  font-size: 11px;
  color: #64748b;
  margin: 0;
  line-height: 1.4;
}

.nested-empty {
  padding: 16px;
  text-align: center;
  font-size: 12px;
  color: #64748b;
}
</style>

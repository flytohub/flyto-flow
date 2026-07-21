<template>
  <div class="rating-preview">
    <PreviewLabel
      v-if="!hideLabel"
      :label="component.label"
      :required="component.validation?.required"
    />
    <div class="rating-container">
      <button
        v-for="n in maxRating"
        :key="n"
        type="button"
        :class="['rating-star', { active: n <= localValue, disabled: !editable }]"
        :disabled="!editable"
        @click="handleClick(n)"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
        </svg>
      </button>
      <span v-if="showValue" class="rating-value">{{ localValue }} / {{ maxRating }}</span>
    </div>
    <PreviewHelp :text="component.helpText" />
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import PreviewLabel from '@/components/common/PreviewLabel.vue'
import PreviewHelp from '@/components/common/PreviewHelp.vue'

const props = defineProps({
  component: {
    type: Object,
    required: true
  },
  editable: {
    type: Boolean,
    default: true
  },
  hideLabel: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update', 'focus', 'blur'])

const localValue = ref(props.component.default || 0)

const maxRating = computed(() => props.component.max || 5)
const showValue = computed(() => props.component.showValue !== false)

watch(() => props.component.default, (newVal) => {
  localValue.value = newVal || 0
})

function handleClick(value) {
  if (!props.editable) return
  localValue.value = value === localValue.value ? 0 : value
  emit('update', { field: 'default', value: localValue.value })
}
</script>

<style scoped>
.rating-preview {
  width: 100%;
}

.rating-container {
  display: flex;
  align-items: center;
  gap: 4px;
}

.rating-star {
  background: none;
  border: none;
  padding: 2px;
  cursor: pointer;
  color: #475569;
  transition: all 0.15s;
}

.rating-star:hover:not(.disabled) {
  transform: scale(1.15);
}

.rating-star.active {
  color: #FBBF24;
}

.rating-star.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.rating-value {
  margin-left: 12px;
  font-size: 13px;
  color: #94a3b8;
}
</style>

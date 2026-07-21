<template>
  <div class="rating-container">
    <button
      v-for="i in maxRating"
      :key="i"
      type="button"
      :class="['rating-star', { filled: i <= modelValue }]"
      :disabled="disabled"
      @click="$emit('update:modelValue', i)"
    >
      <Star :size="20" />
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Star } from 'lucide-vue-next'

const props = defineProps({
  component: { type: Object, required: true },
  modelValue: { type: Number, default: 0 },
  disabled: { type: Boolean, default: false },
})

defineEmits(['update:modelValue'])

const maxRating = computed(() => props.component.props?.max ?? 5)
</script>

<style scoped>
@import './fieldStyles.css';
</style>

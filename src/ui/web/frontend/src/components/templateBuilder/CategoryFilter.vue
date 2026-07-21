<template>
  <div class="category-filter">
    <button
      v-for="category in categories"
      :key="category"
      @click="$emit('update:modelValue', category)"
      :class="['category-btn', { active: modelValue === category }]"
    >
      {{ category }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  categories: {
    type: Array,
    required: true
  }
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.category-filter {
  display: flex;
  gap: 8px;
  padding: 12px 20px;
  border-bottom: 1px solid #334155;
  overflow-x: auto;
}

.category-btn {
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid #475569;
  background: transparent;
  color: #94a3b8;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.category-btn:hover {
  border-color: #8B5CF6;
  color: #A78BFA;
}

.category-btn.active {
  background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%);
  border-color: transparent;
  color: white;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
}
</style>

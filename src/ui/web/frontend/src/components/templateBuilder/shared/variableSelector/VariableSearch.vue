<template>
  <div class="var-search">
    <Search :size="14" class="search-icon" />
    <input
      :value="modelValue"
      type="text"
      :placeholder="$t('variableSelector.searchPlaceholder')"
      class="search-input"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <button
      v-if="modelValue"
      class="clear-btn"
      @click="$emit('clear')"
    >
      <X :size="12" />
    </button>
  </div>
</template>

<script setup>
import { Search, X } from 'lucide-vue-next'

defineProps({
  modelValue: { type: String, default: '' }
})

defineEmits(['update:modelValue', 'clear'])
</script>

<style scoped>
.var-search {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(15, 23, 42, 0.4);
  border-bottom: 1px solid rgba(71, 85, 105, 0.2);
}

.search-icon {
  color: #475569;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #e2e8f0;
  font-size: 13px;
}

.search-input::placeholder {
  color: #475569;
}

.clear-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: rgba(71, 85, 105, 0.4);
  border: none;
  border-radius: 4px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.clear-btn:hover {
  background: rgba(239, 68, 68, 0.3);
  color: #f87171;
}
</style>

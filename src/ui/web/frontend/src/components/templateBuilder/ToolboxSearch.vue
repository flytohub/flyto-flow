<template>
  <div class="toolbox-search">
    <Search :size="16" class="search-icon" />
    <AppInput
      :modelValue="modelValue"
      @update:modelValue="$emit('update:modelValue', $event)"
      :placeholder="$t('templateBuilder.componentToolbox.searchPlaceholder')"
      size="sm"
    />
  </div>
</template>

<script setup>
import { Search } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'

defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.toolbox-search {
  position: relative;
  padding: 16px 20px;
  border-bottom: 1px solid #334155;
}

.search-icon {
  position: absolute;
  left: 34px;
  top: 50%;
  transform: translateY(-50%);
  color: #64748b;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 10px 12px 10px 40px;
  border: 1px solid #475569;
  border-radius: 10px;
  background: #1e293b;
  color: #f1f5f9;
  font-size: 13px;
  transition: all 0.2s;
}

.search-input::placeholder {
  color: #64748b;
}

.search-input:focus {
  outline: none;
  border-color: #8B5CF6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}
</style>

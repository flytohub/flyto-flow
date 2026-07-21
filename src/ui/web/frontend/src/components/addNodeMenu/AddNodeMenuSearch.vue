<template>
  <div class="relative flex-1 group">
    <div class="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-blue-500/20 rounded-xl opacity-0 group-focus-within:opacity-100 blur transition-opacity"></div>
    <div class="relative">
      <Search :size="18" class="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-500 group-focus-within:text-purple-400 transition-colors" />
      <AppInput
        :modelValue="modelValue"
        @update:modelValue="$emit('update:modelValue', $event)"
        :placeholder="$t('workflow.addNode.searchPlaceholder')"
        class="!pl-11"
        ref="inputRef"
        @keydown.esc="$emit('close')"
      />
      <kbd v-if="!modelValue" class="absolute right-3 top-1/2 -translate-y-1/2 px-1.5 py-0.5 bg-white/5 border border-white/10 rounded text-[10px] font-mono text-gray-500">ESC</kbd>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'

defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

defineEmits(['update:modelValue', 'close'])

const inputRef = ref(null)

defineExpose({
  focus: () => inputRef.value?.focus()
})
</script>

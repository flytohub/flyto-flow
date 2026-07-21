<template>
  <div class="relative">
    <button
      @click="isMenuOpen = !isMenuOpen"
      :disabled="loading"
      class="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
    >
      <Download :size="16" />
      {{ $t('audit.export.button', 'Export') }}
      <ChevronDown :size="14" />
    </button>

    <!-- Dropdown Menu -->
    <div
      v-if="isMenuOpen"
      class="absolute right-0 mt-2 w-48 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-10"
    >
      <button
        @click="handleExport('csv')"
        class="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors flex items-center gap-2"
      >
        <FileSpreadsheet :size="16" />
        {{ $t('audit.export.csv', 'Export as CSV') }}
      </button>
      <button
        @click="handleExport('json')"
        class="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors flex items-center gap-2"
      >
        <FileJson :size="16" />
        {{ $t('audit.export.json', 'Export as JSON') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Download, ChevronDown, FileSpreadsheet, FileJson } from 'lucide-vue-next'

defineProps({
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['export'])

const isMenuOpen = ref(false)

function handleExport(format) {
  isMenuOpen.value = false
  emit('export', format)
}

// Close menu on click outside - with proper cleanup
function handleClickOutside(e) {
  if (!e.target.closest('.relative')) {
    isMenuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

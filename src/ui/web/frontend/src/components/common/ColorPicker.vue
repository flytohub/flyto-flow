<template>
  <div class="color-picker w-full">
    <!-- Color Preview & Hex Input Row -->
    <div class="flex items-center gap-2 mb-2">
      <div
        class="color-preview"
        :style="{ backgroundColor: modelValue || defaultColor }"
      >
        <Palette :size="12" class="text-white/80" />
      </div>
      <input
        :value="modelValue || defaultColor"
        @input="handleHexInput"
        type="text"
        placeholder="#8B5CF6"
        class="w-20 px-2 py-1 text-xs font-mono bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-600 rounded text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-purple-500 uppercase"
        maxlength="7"
      />
      <input
        type="color"
        :value="modelValue || defaultColor"
        @input="e => selectColor(e.target.value)"
        class="color-input-native"
        :title="t('colorPicker.custom')"
      />
    </div>

    <!-- Preset Colors -->
    <div class="p-2 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
      <div class="text-[10px] text-gray-500 dark:text-gray-400 mb-1 font-medium">{{ t('colorPicker.presets') }}</div>
      <div class="grid grid-cols-6 gap-1 mb-2">
        <button
          v-for="color in presetColors"
          :key="color"
          type="button"
          @click="selectColor(color)"
          class="color-swatch"
          :class="{ 'ring-2 ring-purple-500 ring-offset-1 dark:ring-offset-gray-800': modelValue === color }"
          :style="{ backgroundColor: color }"
          :aria-label="color"
        >
          <Check v-if="modelValue === color" :size="8" class="text-white" />
        </button>
      </div>
      <div class="text-[10px] text-gray-500 dark:text-gray-400 mb-1 font-medium">{{ t('colorPicker.popular') }}</div>
      <div class="grid grid-cols-6 gap-1">
        <button
          v-for="color in popularColors"
          :key="color"
          type="button"
          @click="selectColor(color)"
          class="color-swatch"
          :class="{ 'ring-2 ring-purple-500 ring-offset-1 dark:ring-offset-gray-800': modelValue === color }"
          :style="{ backgroundColor: color }"
          :aria-label="color"
        >
          <Check v-if="modelValue === color" :size="8" class="text-white" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { Palette, Check } from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  defaultColor: {
    type: String,
    default: '#8B5CF6'
  }
})

const emit = defineEmits(['update:modelValue'])

// Preset colors - 6 columns
const presetColors = [
  '#EF4444', '#F97316', '#F59E0B', '#84CC16', '#22C55E', '#14B8A6',
  '#06B6D4', '#3B82F6', '#6366F1', '#8B5CF6', '#A855F7', '#EC4899',
]

// Popular colors
const popularColors = [
  '#000000', '#374151', '#6B7280', '#9CA3AF', '#D1D5DB', '#FFFFFF',
]

function selectColor(color) {
  emit('update:modelValue', color.toUpperCase())
}

function handleHexInput(e) {
  let value = e.target.value.trim()
  if (!value.startsWith('#')) {
    value = '#' + value
  }
  if (/^#[0-9A-Fa-f]{6}$/.test(value)) {
    emit('update:modelValue', value.toUpperCase())
  }
}
</script>

<style scoped>
.color-preview {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.color-swatch {
  aspect-ratio: 1;
  width: 100%;
  border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.color-swatch:hover {
  transform: scale(1.15);
  z-index: 1;
}

.color-swatch[style*="background-color: #FFFFFF"],
.color-swatch[style*="background-color: rgb(255, 255, 255)"] {
  border-color: #d1d5db;
}

.color-input-native {
  width: 26px;
  height: 26px;
  padding: 0;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  background: transparent;
  flex-shrink: 0;
}

.color-input-native::-webkit-color-swatch-wrapper {
  padding: 0;
}

.color-input-native::-webkit-color-swatch {
  border: 1px solid #d1d5db;
  border-radius: 4px;
}
</style>

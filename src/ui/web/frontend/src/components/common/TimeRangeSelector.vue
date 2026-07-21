<template>
  <div class="relative">
    <button
      @click="toggleDropdown"
      class="flex items-center gap-2 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white hover:bg-gray-600 transition-colors"
    >
      <Calendar :size="16" class="text-gray-400" />
      <span>{{ selectedLabel }}</span>
      <ChevronDown :size="16" class="text-gray-400" :class="{ 'rotate-180': isOpen }" />
    </button>

    <!-- Dropdown -->
    <Transition name="dropdown">
      <div
        v-if="isOpen"
        class="absolute right-0 top-full mt-2 w-64 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50"
      >
        <!-- Presets -->
        <div class="p-2 border-b border-gray-700">
          <button
            v-for="preset in presets"
            :key="preset.value"
            @click="selectPreset(preset)"
            :class="[
              'w-full px-3 py-2 text-left rounded-lg text-sm transition-colors',
              selectedPreset === preset.value
                ? 'bg-purple-600/20 text-purple-400'
                : 'text-gray-300 hover:bg-gray-700'
            ]"
          >
            {{ preset.label }}
          </button>
        </div>

        <!-- Custom Range -->
        <div v-if="showCustom" class="p-4 space-y-3">
          <h4 class="text-xs font-medium text-gray-400 uppercase">
            {{ $t('common.timeRange.custom', 'Custom Range') }}
          </h4>

          <div class="space-y-2">
            <label class="block">
              <span class="text-xs text-gray-400">{{ $t('common.timeRange.from', 'From') }}</span>
              <input
                type="datetime-local"
                v-model="customFrom"
                class="w-full mt-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-sm text-white"
              />
            </label>
            <label class="block">
              <span class="text-xs text-gray-400">{{ $t('common.timeRange.to', 'To') }}</span>
              <input
                type="datetime-local"
                v-model="customTo"
                class="w-full mt-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-sm text-white"
              />
            </label>
          </div>

          <button
            @click="applyCustomRange"
            :disabled="!isCustomValid"
            class="w-full px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ $t('common.apply', 'Apply') }}
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { Calendar, ChevronDown } from 'lucide-vue-next'

const props = defineProps({
  /**
   * v-model value: { from: Date, to: Date, preset?: string }
   */
  modelValue: {
    type: Object,
    default: () => ({ from: null, to: null, preset: '24h' })
  },
  /**
   * Show custom date picker
   */
  showCustom: {
    type: Boolean,
    default: true
  },
  /**
   * Available presets
   */
  availablePresets: {
    type: Array,
    default: () => ['1h', '6h', '24h', '7d', '30d']
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const { t } = useI18n()

const isOpen = ref(false)
const customFrom = ref('')
const customTo = ref('')

const presetOptions = {
  '1h': { label: t('common.timeRange.1h', 'Last 1 hour'), hours: 1 },
  '6h': { label: t('common.timeRange.6h', 'Last 6 hours'), hours: 6 },
  '24h': { label: t('common.timeRange.24h', 'Last 24 hours'), hours: 24 },
  '7d': { label: t('common.timeRange.7d', 'Last 7 days'), days: 7 },
  '30d': { label: t('common.timeRange.30d', 'Last 30 days'), days: 30 },
  '90d': { label: t('common.timeRange.90d', 'Last 90 days'), days: 90 }
}

const presets = computed(() => {
  return props.availablePresets
    .filter(p => presetOptions[p])
    .map(p => ({ value: p, label: presetOptions[p].label }))
})

const selectedPreset = computed(() => props.modelValue?.preset || null)

const selectedLabel = computed(() => {
  if (selectedPreset.value && presetOptions[selectedPreset.value]) {
    return presetOptions[selectedPreset.value].label
  }
  if (props.modelValue?.from && props.modelValue?.to) {
    return t('common.timeRange.customLabel', 'Custom Range')
  }
  return t('common.timeRange.selectRange', 'Select Range')
})

const isCustomValid = computed(() => {
  if (!customFrom.value || !customTo.value) return false
  return new Date(customFrom.value) < new Date(customTo.value)
})

function toggleDropdown() {
  isOpen.value = !isOpen.value
}

function closeDropdown() {
  isOpen.value = false
}

function selectPreset(preset) {
  const now = new Date()
  const to = now
  let from = new Date(now)

  const config = presetOptions[preset.value]
  if (config.hours) {
    from.setHours(from.getHours() - config.hours)
  } else if (config.days) {
    from.setDate(from.getDate() - config.days)
  }

  const value = { from, to, preset: preset.value }
  emit('update:modelValue', value)
  emit('change', value)
  closeDropdown()
}

function applyCustomRange() {
  if (!isCustomValid.value) return

  const value = {
    from: new Date(customFrom.value),
    to: new Date(customTo.value),
    preset: null
  }
  emit('update:modelValue', value)
  emit('change', value)
  closeDropdown()
}

// Close on outside click
function handleClickOutside(event) {
  const el = event.target.closest('.relative')
  if (!el) closeDropdown()
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

// Initialize custom inputs from model value
watch(() => props.modelValue, (val) => {
  if (val?.from && !val?.preset) {
    customFrom.value = formatDateTimeLocal(val.from)
  }
  if (val?.to && !val?.preset) {
    customTo.value = formatDateTimeLocal(val.to)
  }
}, { immediate: true })

function formatDateTimeLocal(date) {
  if (!date) return ''
  const d = new Date(date)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}
</script>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s, transform 0.15s;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>

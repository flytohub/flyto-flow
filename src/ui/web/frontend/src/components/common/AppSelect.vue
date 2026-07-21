<template>
  <div ref="containerRef" class="relative w-full" :class="{ 'opacity-50 pointer-events-none': disabled }">
    <button
      type="button"
      :class="triggerClasses"
      :disabled="disabled"
      :aria-expanded="isOpen"
      aria-haspopup="listbox"
      @click="toggle"
      @keydown.escape="close"
      @keydown.enter.prevent="toggle"
      @keydown.space.prevent="toggle"
      @keydown.down.prevent="openAndFocusFirst"
      @keydown.up.prevent="openAndFocusLast"
    >
      <span
        class="flex-1 truncate text-left"
        :class="hasSelection ? 'text-gray-900 dark:text-white' : 'text-gray-400 dark:text-gray-500'"
      >
        {{ displayLabel }}
      </span>
      <ChevronDown
        :size="size === 'sm' ? 14 : 16"
        class="flex-shrink-0 ml-2 text-gray-400 transition-transform duration-200"
        :class="isOpen ? 'rotate-180' : ''"
      />
    </button>

    <Transition
      enter-active-class="transition-all duration-150 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition-all duration-100 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="isOpen"
        ref="dropdownRef"
        class="absolute left-0 right-0 z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg dark:shadow-black/30 max-h-60 overflow-y-auto py-1"
        :class="dropDirection === 'drop-up' ? 'bottom-full mb-1.5' : 'top-full mt-1.5'"
        @keydown.escape="close"
      >
        <ul role="listbox">
          <li
            v-for="(opt, idx) in normalizedOptions"
            :key="idx"
            role="option"
            :aria-selected="isSelected(opt.value)"
            class="flex items-center justify-between w-full px-3 py-2 text-sm text-left cursor-pointer transition-colors"
            :class="[
              isSelected(opt.value)
                ? 'bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
            ]"
            @click="select(opt.value)"
            @mouseenter="focusedIndex = idx"
          >
            <span class="truncate">{{ opt.label }}</span>
            <Check
              v-if="isSelected(opt.value)"
              :size="14"
              class="flex-shrink-0 ml-2 text-purple-500"
            />
          </li>
        </ul>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { ChevronDown, Check } from 'lucide-vue-next'

const props = defineProps({
  modelValue: {
    type: [String, Number, Boolean, Array],
    default: ''
  },
  multiple: {
    type: Boolean,
    default: false
  },
  options: {
    type: Array,
    default: () => []
  },
  placeholder: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  size: {
    type: String,
    default: 'md',
    validator: v => ['sm', 'md'].includes(v)
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const containerRef = ref(null)
const dropdownRef = ref(null)
const isOpen = ref(false)
const focusedIndex = ref(-1)
const dropDirection = ref('drop-down')

const normalizedOptions = computed(() =>
  props.options.map(opt =>
    typeof opt === 'object' ? opt : { value: opt, label: String(opt) }
  )
)

const selectedOption = computed(() => {
  if (props.multiple) {
    const vals = Array.isArray(props.modelValue) ? props.modelValue : []
    return normalizedOptions.value.filter(o => vals.includes(o.value))
  }
  return normalizedOptions.value.find(o => o.value === props.modelValue)
})

const hasSelection = computed(() => {
  if (props.multiple) return Array.isArray(props.modelValue) && props.modelValue.length > 0
  return selectedOption.value != null && props.modelValue !== ''
})

const displayLabel = computed(() => {
  if (props.multiple) {
    const selected = Array.isArray(selectedOption.value) ? selectedOption.value : []
    if (selected.length === 0) return props.placeholder || '\u00A0'
    if (selected.length <= 2) return selected.map(o => o.label).join(', ')
    return `${selected[0].label} +${selected.length - 1}`
  }
  if (selectedOption.value) return selectedOption.value.label
  return props.placeholder || '\u00A0'
})

const triggerClasses = computed(() => {
  const base = 'flex items-center w-full bg-white dark:bg-gray-800 border rounded-lg text-left cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:ring-offset-1 disabled:cursor-not-allowed'
  const border = isOpen.value
    ? 'border-purple-500 ring-2 ring-purple-500/20'
    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
  const sizing = props.size === 'sm'
    ? 'px-3 py-1.5 text-sm min-h-[34px]'
    : 'px-4 py-2.5 text-sm min-h-[42px]'
  return [base, border, sizing]
})

function isSelected(value) {
  if (props.multiple) {
    return Array.isArray(props.modelValue) && props.modelValue.includes(value)
  }
  return props.modelValue === value
}

function toggle() {
  if (props.disabled) return
  isOpen.value ? close() : open()
}

function open() {
  isOpen.value = true
  if (props.multiple) {
    focusedIndex.value = 0
  } else {
    focusedIndex.value = normalizedOptions.value.findIndex(o => o.value === props.modelValue)
  }
  nextTick(updateDropDirection)
}

function close() {
  isOpen.value = false
  focusedIndex.value = -1
}

function select(value) {
  if (props.multiple) {
    const current = Array.isArray(props.modelValue) ? [...props.modelValue] : []
    const idx = current.indexOf(value)
    if (idx >= 0) {
      current.splice(idx, 1)
    } else {
      current.push(value)
    }
    emit('update:modelValue', current)
    emit('change', current)
    // Don't close in multi mode — let user pick more
    return
  }
  emit('update:modelValue', value)
  emit('change', value)
  close()
}

function openAndFocusFirst() {
  if (!isOpen.value) open()
  focusedIndex.value = 0
}

function openAndFocusLast() {
  if (!isOpen.value) open()
  focusedIndex.value = normalizedOptions.value.length - 1
}

function updateDropDirection() {
  if (!containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  const spaceBelow = window.innerHeight - rect.bottom
  dropDirection.value = spaceBelow < 240 ? 'drop-up' : 'drop-down'
}

function onClickOutside(e) {
  if (containerRef.value && !containerRef.value.contains(e.target)) {
    close()
  }
}

watch(isOpen, (val) => {
  if (val) {
    document.addEventListener('click', onClickOutside, true)
  } else {
    document.removeEventListener('click', onClickOutside, true)
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onClickOutside, true)
})
</script>

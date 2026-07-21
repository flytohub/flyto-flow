<template>
  <div class="flex flex-wrap gap-2">
    <button
      v-for="label in labels"
      :key="label.key"
      type="button"
      class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-all duration-200 cursor-pointer select-none"
      :class="[
        isSelected(label.key)
          ? label.activeClasses
          : 'bg-gray-500/10 text-gray-500 border-gray-500/20 opacity-50 hover:opacity-75'
      ]"
      @click="toggle(label.key)"
    >
      <span
        class="w-2 h-2 rounded-full"
        :class="label.dotClass"
        aria-hidden="true"
      />
      {{ label.name }}
    </button>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

const labels = [
  {
    key: 'enhancement',
    name: 'enhancement',
    activeClasses: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    dotClass: 'bg-blue-400'
  },
  {
    key: 'bugfix',
    name: 'bugfix',
    activeClasses: 'bg-red-500/20 text-red-400 border-red-500/30',
    dotClass: 'bg-red-400'
  },
  {
    key: 'docs',
    name: 'docs',
    activeClasses: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    dotClass: 'bg-emerald-400'
  },
  {
    key: 'breaking',
    name: 'breaking',
    activeClasses: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    dotClass: 'bg-orange-400'
  },
  {
    key: 'performance',
    name: 'performance',
    activeClasses: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    dotClass: 'bg-purple-400'
  }
]

function isSelected(key) {
  return props.modelValue.includes(key)
}

function toggle(key) {
  const selected = [...props.modelValue]
  const index = selected.indexOf(key)
  if (index === -1) {
    selected.push(key)
  } else {
    selected.splice(index, 1)
  }
  emit('update:modelValue', selected)
}
</script>

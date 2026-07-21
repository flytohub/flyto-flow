<template>
  <div class="font-mono text-xs">
    <div v-if="isObject" class="space-y-1">
      <div v-for="(value, key) in data" :key="key" class="flex">
        <span class="text-purple-400 flex-shrink-0">{{ key }}:</span>
        <span class="ml-2">
          <template v-if="isPrimitive(value)">
            <span :class="getValueClass(value)">{{ formatValue(value) }}</span>
          </template>
          <template v-else-if="Array.isArray(value)">
            <button
              v-if="!isExpanded(key)"
              @click="toggle(key)"
              class="text-gray-500 hover:text-gray-300"
            >
              [{{ value.length }}]
            </button>
            <div v-else>
              <button @click="toggle(key)" class="text-gray-500 hover:text-gray-300">[</button>
              <div class="ml-4 border-l border-gray-700 pl-2">
                <div v-for="(item, index) in value" :key="index">
                  <span class="text-gray-500">{{ index }}:</span>
                  <span class="ml-1">
                    <template v-if="isPrimitive(item)">
                      <span :class="getValueClass(item)">{{ formatValue(item) }}</span>
                    </template>
                    <JsonViewer v-else :data="item" :depth="depth + 1" />
                  </span>
                </div>
              </div>
              <span class="text-gray-500">]</span>
            </div>
          </template>
          <template v-else>
            <button
              v-if="!isExpanded(key)"
              @click="toggle(key)"
              class="text-gray-500 hover:text-gray-300"
            >
              {...}
            </button>
            <div v-else>
              <button @click="toggle(key)" class="text-gray-500 hover:text-gray-300">{</button>
              <div class="ml-4 border-l border-gray-700 pl-2">
                <JsonViewer :data="value" :depth="depth + 1" />
              </div>
              <span class="text-gray-500">}</span>
            </div>
          </template>
        </span>
      </div>
    </div>
    <div v-else-if="Array.isArray(data)">
      <div v-for="(item, index) in data" :key="index">
        <span class="text-gray-500">{{ index }}:</span>
        <span class="ml-1">
          <template v-if="isPrimitive(item)">
            <span :class="getValueClass(item)">{{ formatValue(item) }}</span>
          </template>
          <JsonViewer v-else :data="item" :depth="depth + 1" />
        </span>
      </div>
    </div>
    <span v-else :class="getValueClass(data)">{{ formatValue(data) }}</span>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  data: {
    type: [Object, Array, String, Number, Boolean, null],
    default: null
  },
  depth: {
    type: Number,
    default: 0
  }
})

const expanded = ref({})

const isObject = computed(() => {
  return props.data !== null && typeof props.data === 'object' && !Array.isArray(props.data)
})

function isExpanded(key) {
  return expanded.value[key] ?? (props.depth < 2)
}

function toggle(key) {
  expanded.value[key] = !isExpanded(key)
}

function isPrimitive(value) {
  return value === null || typeof value !== 'object'
}

function getValueClass(value) {
  if (value === null) return 'text-gray-500'
  if (typeof value === 'boolean') return value ? 'text-green-400' : 'text-red-400'
  if (typeof value === 'number') return 'text-blue-400'
  if (typeof value === 'string') return 'text-yellow-400'
  return 'text-white'
}

function formatValue(value) {
  if (value === null) return 'null'
  if (typeof value === 'string') return `"${value.length > 100 ? value.slice(0, 100) + '...' : value}"`
  return String(value)
}
</script>

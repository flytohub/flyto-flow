<template>
  <div class="bg-gray-800 rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-700">
      <div class="flex items-center gap-2">
        <Database :size="18" class="text-purple-400" />
        <h3 class="text-sm font-medium text-white">{{ $t('variables.title') }}</h3>
        <span v-if="variables.length" class="text-xs text-gray-500">({{ variables.length }})</span>
      </div>
      <button
        @click="$emit('create')"
        class="flex items-center gap-1 px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg transition-colors"
      >
        <Plus :size="14" />
        {{ $t('variables.create') }}
      </button>
    </div>

    <!-- Search -->
    <div class="p-3 border-b border-gray-700">
      <div class="relative">
        <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
        <AppInput
          v-model="searchQuery"
          :placeholder="$t('common.search') + '...'"
          class="!pl-9"
        />
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="p-8 flex items-center justify-center">
      <Loader :size="24" class="text-purple-400 animate-spin" />
    </div>

    <!-- Empty State -->
    <div v-else-if="!filteredVariables.length" class="p-8 text-center text-gray-400">
      <Database :size="32" class="mx-auto mb-2 opacity-50" />
      <p>{{ $t('variables.noVariables') }}</p>
    </div>

    <!-- Variable List -->
    <div v-else class="divide-y divide-gray-700 max-h-96 overflow-y-auto">
      <div
        v-for="variable in filteredVariables"
        :key="variable.id"
        class="p-4 hover:bg-gray-700/30 transition-colors cursor-pointer"
        @click="$emit('select', variable)"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-white">{{ variable.name }}</span>
              <span
                class="px-1.5 py-0.5 text-xs rounded"
                :class="getTypeClass(variable.type)"
              >
                {{ $t(`variables.types.${variable.type}`) }}
              </span>
            </div>
            <div class="flex items-center gap-3 mt-1 text-xs text-gray-500">
              <span class="flex items-center gap-1">
                <Layers :size="12" />
                {{ $t(`variables.scopes.${variable.scope}`) }}
              </span>
              <span class="flex items-center gap-1">
                <Globe :size="12" />
                {{ $t(`variables.environments.${variable.environment}`) }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-1">
            <button
              @click.stop="$emit('edit', variable)"
              aria-label="Edit variable"
              class="p-1.5 text-gray-400 hover:text-white transition-colors"
            >
              <Pencil :size="14" />
            </button>
            <button
              @click.stop="$emit('delete', variable)"
              aria-label="Delete variable"
              class="p-1.5 text-gray-400 hover:text-red-400 transition-colors"
            >
              <Trash2 :size="14" />
            </button>
          </div>
        </div>
        <div v-if="variable.type !== 'secret'" class="mt-2">
          <code class="text-xs text-gray-400 bg-gray-900 px-2 py-1 rounded">
            {{ formatValue(variable.value) }}
          </code>
        </div>
        <div v-else class="mt-2">
          <code class="text-xs text-gray-500 bg-gray-900 px-2 py-1 rounded">
            ••••••••
          </code>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Database,
  Plus,
  Search,
  Loader,
  Layers,
  Globe,
  Pencil,
  Trash2
} from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'

const props = defineProps({
  variables: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['create', 'select', 'edit', 'delete'])
const { t } = useI18n()

const searchQuery = ref('')

const filteredVariables = computed(() => {
  if (!searchQuery.value) return props.variables
  const query = searchQuery.value.toLowerCase()
  return props.variables.filter(v =>
    v.name.toLowerCase().includes(query) ||
    v.scope.toLowerCase().includes(query)
  )
})

function getTypeClass(type) {
  const classes = {
    string: 'bg-blue-900/50 text-blue-300',
    number: 'bg-green-900/50 text-green-300',
    boolean: 'bg-yellow-900/50 text-yellow-300',
    json: 'bg-purple-900/50 text-purple-300',
    ['secret']: 'bg-red-900/50 text-red-300'
  }
  return classes[type] || 'bg-gray-700 text-gray-300'
}

function formatValue(value) {
  if (typeof value === 'object') {
    return JSON.stringify(value).slice(0, 50) + (JSON.stringify(value).length > 50 ? '...' : '')
  }
  const str = String(value)
  return str.length > 50 ? str.slice(0, 50) + '...' : str
}
</script>

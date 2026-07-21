<template>
  <div class="flex items-center gap-3 mb-6 flex-wrap">
    <!-- Status Tabs -->
    <div class="flex items-center bg-gray-800/50 backdrop-blur-xl rounded-xl border border-white/10 p-1">
      <button
        v-for="tab in statusTabs"
        :key="tab.value"
        @click="$emit('update:filterStatus', tab.value)"
        :class="[
          'px-4 py-1.5 text-sm font-medium rounded-lg transition-all',
          filterStatus === tab.value
            ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/30'
            : 'text-gray-400 hover:text-white'
        ]"
      >
        {{ $t(tab.label, tab.fallback) }}
      </button>
    </div>

    <!-- Type Filter -->
    <div class="relative" ref="typeDropdownRef">
      <button
        @click="$emit('toggle-type-dropdown')"
        class="flex items-center gap-2 px-3 py-2 bg-gray-800/50 backdrop-blur-xl border border-white/10 rounded-xl text-sm text-gray-300 hover:border-purple-500/30 transition-colors"
      >
        {{ filterType ? $t(`issues.type.${filterType}`, filterType) : $t('issues.allTypes', 'All types') }}
        <ChevronDown :size="14" />
      </button>
      <div
        v-if="typeDropdownOpen"
        class="absolute top-full left-0 mt-2 w-44 bg-gray-800/90 backdrop-blur-2xl border border-white/10 rounded-xl shadow-2xl z-10 overflow-hidden"
      >
        <button
          @click="$emit('update:filterType', null); $emit('close-type-dropdown')"
          class="w-full text-left px-4 py-2.5 text-sm text-gray-300 hover:bg-purple-500/20 hover:text-white transition-colors"
        >
          {{ $t('issues.allTypes', 'All types') }}
        </button>
        <button
          v-for="t in typeOptions"
          :key="t"
          @click="$emit('update:filterType', t); $emit('close-type-dropdown')"
          class="w-full text-left px-4 py-2.5 text-sm text-gray-300 hover:bg-purple-500/20 hover:text-white transition-colors flex items-center gap-2"
        >
          <component :is="typeIcon(t)" :size="14" />
          {{ $t(`issues.type.${t}`, t) }}
        </button>
      </div>
    </div>

    <!-- Sort -->
    <div class="relative" ref="sortDropdownRef">
      <button
        @click="$emit('toggle-sort-dropdown')"
        class="flex items-center gap-2 px-3 py-2 bg-gray-800/50 backdrop-blur-xl border border-white/10 rounded-xl text-sm text-gray-300 hover:border-purple-500/30 transition-colors"
      >
        {{ $t(`issues.sort.${sortBy}`, sortBy) }}
        <ChevronDown :size="14" />
      </button>
      <div
        v-if="sortDropdownOpen"
        class="absolute top-full left-0 mt-2 w-52 bg-gray-800/90 backdrop-blur-2xl border border-white/10 rounded-xl shadow-2xl z-10 overflow-hidden"
      >
        <button
          v-for="s in sortOptions"
          :key="s"
          @click="$emit('update:sortBy', s); $emit('close-sort-dropdown')"
          class="w-full text-left px-4 py-2.5 text-sm text-gray-300 hover:bg-purple-500/20 hover:text-white transition-colors"
        >
          {{ $t(`issues.sort.${s}`, s) }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ChevronDown } from 'lucide-vue-next'
import { CircleDot, Bug, Lightbulb, HelpCircle } from 'lucide-vue-next'

defineProps({
  filterStatus: { default: 'open' },
  filterType: { default: null },
  sortBy: { type: String, default: 'newest' },
  typeDropdownOpen: { type: Boolean, default: false },
  sortDropdownOpen: { type: Boolean, default: false },
  statusTabs: { type: Array, required: true },
  typeOptions: { type: Array, required: true },
  sortOptions: { type: Array, required: true },
})

defineEmits([
  'update:filterStatus',
  'update:filterType',
  'update:sortBy',
  'toggle-type-dropdown',
  'toggle-sort-dropdown',
  'close-type-dropdown',
  'close-sort-dropdown',
])

function typeIcon(type) {
  switch (type) {
    case 'bug': return Bug
    case 'feature': return Lightbulb
    case 'question': return HelpCircle
    default: return CircleDot
  }
}
</script>

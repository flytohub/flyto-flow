<template>
  <div class="group relative bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6 hover:border-orange-500/30 transition-all duration-500">
    <div class="absolute inset-0 bg-gradient-to-br from-orange-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
    <div class="relative">
      <!-- Header -->
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center">
          <Globe :size="20" class="text-white" />
        </div>
        <div>
          <h2 class="text-lg font-semibold text-white">{{ $t('publish.regions.title') }}</h2>
          <p class="text-sm text-gray-400">{{ $t('publish.regions.subtitle') }}</p>
        </div>
      </div>

      <!-- Global/Regional Toggle -->
      <div class="mb-6">
        <div class="flex gap-3">
          <button
            @click="setGlobal(true)"
            :class="[
              'flex-1 p-4 rounded-xl border transition-all',
              isGlobal
                ? 'bg-orange-500/20 border-orange-500/50 text-orange-400'
                : 'bg-gray-900/50 border-white/10 text-gray-400 hover:border-white/20'
            ]"
          >
            <Globe2 :size="24" class="mx-auto mb-2" />
            <div class="font-medium">{{ $t('publish.regions.global') }}</div>
            <div class="text-xs mt-1 opacity-70">{{ $t('publish.regions.globalDesc') }}</div>
          </button>
          <button
            @click="setGlobal(false)"
            :class="[
              'flex-1 p-4 rounded-xl border transition-all',
              !isGlobal
                ? 'bg-orange-500/20 border-orange-500/50 text-orange-400'
                : 'bg-gray-900/50 border-white/10 text-gray-400 hover:border-white/20'
            ]"
          >
            <MapPin :size="24" class="mx-auto mb-2" />
            <div class="font-medium">{{ $t('publish.regions.specific') }}</div>
            <div class="text-xs mt-1 opacity-70">{{ $t('publish.regions.specificDesc') }}</div>
          </button>
        </div>
      </div>

      <!-- Region Selection (when not global) -->
      <div v-if="!isGlobal" class="space-y-4">
        <!-- Visibility Regions -->
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">
            {{ $t('publish.regions.availableIn') }}
          </label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="region in availableRegions"
              :key="region.code"
              @click="toggleVisibilityRegion(region.code)"
              :aria-label="'Toggle ' + region.name"
              :class="[
                'px-3 py-2 rounded-lg text-sm font-medium transition-all',
                visibilityRegions.includes(region.code)
                  ? 'bg-green-500/20 border border-green-500/50 text-green-400'
                  : 'bg-gray-900/50 border border-white/10 text-gray-400 hover:border-white/20'
              ]"
            >
              <span class="mr-1">{{ region.flag }}</span>
              {{ region.name }}
            </button>
          </div>
          <p class="text-xs text-gray-500 mt-2">{{ $t('publish.regions.availableInHint') }}</p>
        </div>

        <!-- Blocked Regions -->
        <div class="mt-6">
          <label class="block text-sm font-medium text-gray-300 mb-2">
            {{ $t('publish.regions.blockedIn') }}
          </label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="region in availableRegions"
              :key="region.code"
              @click="toggleBlockedRegion(region.code)"
              :disabled="visibilityRegions.includes(region.code)"
              :aria-label="'Block ' + region.name"
              :class="[
                'px-3 py-2 rounded-lg text-sm font-medium transition-all',
                blockedRegions.includes(region.code)
                  ? 'bg-red-500/20 border border-red-500/50 text-red-400'
                  : visibilityRegions.includes(region.code)
                    ? 'bg-gray-900/50 border border-white/10 text-gray-600 cursor-not-allowed'
                    : 'bg-gray-900/50 border border-white/10 text-gray-400 hover:border-white/20'
              ]"
            >
              <span class="mr-1">{{ region.flag }}</span>
              {{ region.name }}
            </button>
          </div>
          <p class="text-xs text-gray-500 mt-2">{{ $t('publish.regions.blockedInHint') }}</p>
        </div>
      </div>

      <!-- Summary -->
      <div v-if="!isGlobal && (visibilityRegions.length > 0 || blockedRegions.length > 0)" class="mt-6 p-4 bg-gray-900/50 border border-white/10 rounded-xl">
        <div class="text-sm text-gray-400">
          <span v-if="visibilityRegions.length > 0" class="block mb-1">
            <span class="text-green-400">{{ $t('publish.regions.visibleIn') }}:</span>
            {{ visibilityRegions.map(r => getRegionName(r)).join(', ') }}
          </span>
          <span v-if="blockedRegions.length > 0" class="block">
            <span class="text-red-400">{{ $t('publish.regions.blockedIn') }}:</span>
            {{ blockedRegions.map(r => getRegionName(r)).join(', ') }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Globe, Globe2, MapPin } from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps({
  visibilityRegions: {
    type: Array,
    default: () => []
  },
  blockedRegions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:visibilityRegions', 'update:blockedRegions'])

const availableRegions = [
  { code: 'US', name: 'United States', flag: '🇺🇸' },
  { code: 'TW', name: 'Taiwan', flag: '🇹🇼' },
  { code: 'JP', name: 'Japan', flag: '🇯🇵' },
  { code: 'KR', name: 'South Korea', flag: '🇰🇷' },
  { code: 'CN', name: 'China', flag: '🇨🇳' },
  { code: 'HK', name: 'Hong Kong', flag: '🇭🇰' },
  { code: 'SG', name: 'Singapore', flag: '🇸🇬' },
  { code: 'GB', name: 'United Kingdom', flag: '🇬🇧' },
  { code: 'DE', name: 'Germany', flag: '🇩🇪' },
  { code: 'FR', name: 'France', flag: '🇫🇷' },
  { code: 'AU', name: 'Australia', flag: '🇦🇺' },
  { code: 'CA', name: 'Canada', flag: '🇨🇦' },
]

// Track if user explicitly chose regional mode (even with empty selections)
const regionalMode = ref(false)

// Initialize from props: if any regions are set, we're in regional mode
watch(() => [props.visibilityRegions, props.blockedRegions], ([vis, blocked]) => {
  if (vis.length > 0 || blocked.length > 0) {
    regionalMode.value = true
  }
}, { immediate: true })

const isGlobal = computed(() => {
  return !regionalMode.value
})

function setGlobal(global) {
  regionalMode.value = !global
  if (global) {
    emit('update:visibilityRegions', [])
    emit('update:blockedRegions', [])
  }
}

function toggleVisibilityRegion(code) {
  const current = [...props.visibilityRegions]
  const index = current.indexOf(code)

  if (index >= 0) {
    current.splice(index, 1)
  } else {
    current.push(code)
    // Remove from blocked if adding to visible
    const blocked = props.blockedRegions.filter(r => r !== code)
    if (blocked.length !== props.blockedRegions.length) {
      emit('update:blockedRegions', blocked)
    }
  }

  emit('update:visibilityRegions', current)
}

function toggleBlockedRegion(code) {
  // Cannot block a region that's in visibility list
  if (props.visibilityRegions.includes(code)) return

  const current = [...props.blockedRegions]
  const index = current.indexOf(code)

  if (index >= 0) {
    current.splice(index, 1)
  } else {
    current.push(code)
  }

  emit('update:blockedRegions', current)
}

function getRegionName(code) {
  const region = availableRegions.find(r => r.code === code)
  return region ? `${region.flag} ${region.name}` : code
}
</script>

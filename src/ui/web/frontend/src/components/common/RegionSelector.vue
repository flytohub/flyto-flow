<template>
  <div class="relative" ref="dropdownRef">
    <button
      ref="buttonRef"
      @click="toggleDropdown"
      class="flex items-center gap-1.5 px-2 py-1.5 text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors text-sm"
      :aria-label="$t('common.selectRegion')"
    >
      <Globe :size="18" />
      <span class="hidden sm:inline">{{ currentRegionLabel }}</span>
      <ChevronDown :size="14" :class="isOpen ? 'rotate-180' : ''" class="transition-transform" />
    </button>

    <!-- Dropdown Menu - Teleport to body to avoid overflow clipping -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition-all duration-200 ease-out"
        enter-from-class="opacity-0 scale-95 -translate-y-2"
        enter-to-class="opacity-100 scale-100 translate-y-0"
        leave-active-class="transition-all duration-150 ease-in"
        leave-from-class="opacity-100 scale-100 translate-y-0"
        leave-to-class="opacity-0 scale-95 -translate-y-2"
      >
        <div
          v-if="isOpen"
          ref="menuRef"
          :style="dropdownStyle"
          class="fixed w-56 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg z-[9999] overflow-hidden"
        >
          <!-- Search Input -->
          <div class="p-2 border-b border-gray-200 dark:border-gray-700">
            <div class="relative">
              <Search :size="14" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
              <AppInput
                ref="searchInputRef"
                v-model="searchQuery"
                :placeholder="$t('common.search')"
                class="!pl-8"
                @click.stop
              />
            </div>
          </div>

          <!-- Region List -->
          <div class="max-h-64 overflow-y-auto py-1">
            <button
              v-for="region in filteredRegions"
              :key="region.code"
              @click="selectRegion(region.code)"
              :class="[
                'w-full px-3 py-2 text-left text-sm transition-colors flex items-center gap-2',
                selectedRegion === region.code
                  ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              ]"
            >
              <span class="text-base">{{ region.flag }}</span>
              <span>{{ getRegionName(region) }}</span>
              <Check v-if="selectedRegion === region.code" :size="14" class="ml-auto text-primary-500" />
            </button>

            <!-- No Results -->
            <div v-if="filteredRegions.length === 0" class="px-3 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
              {{ $t('common.noResults') }}
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Globe, ChevronDown, Check, Search } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'

const STORAGE_KEY = 'user_region'

const { t } = useI18n()

const isOpen = ref(false)
const dropdownRef = ref(null)
const buttonRef = ref(null)
const menuRef = ref(null)
const searchInputRef = ref(null)
const selectedRegion = ref('')
const searchQuery = ref('')

// Dropdown position
const dropdownStyle = ref({
  top: '0px',
  left: '0px'
})

// Available regions (Global first, then alphabetically sorted)
// Synced with LOCALE_REGION_MAP in i18n/index.js
const regions = [
  { code: '', flag: '🌐', name: 'Global', nameKey: 'common.global' },
  { code: 'CN', flag: '🇨🇳', name: 'China' },
  { code: 'FR', flag: '🇫🇷', name: 'France' },
  { code: 'DE', flag: '🇩🇪', name: 'Germany' },
  { code: 'HK', flag: '🇭🇰', name: 'Hong Kong' },
  { code: 'IN', flag: '🇮🇳', name: 'India' },
  { code: 'IT', flag: '🇮🇹', name: 'Italy' },
  { code: 'JP', flag: '🇯🇵', name: 'Japan' },
  { code: 'PT', flag: '🇵🇹', name: 'Portugal' },
  { code: 'RU', flag: '🇷🇺', name: 'Russia' },
  { code: 'SG', flag: '🇸🇬', name: 'Singapore' },
  { code: 'KR', flag: '🇰🇷', name: 'South Korea' },
  { code: 'ES', flag: '🇪🇸', name: 'Spain' },
  { code: 'TW', flag: '🇹🇼', name: 'Taiwan' },
  { code: 'GB', flag: '🇬🇧', name: 'United Kingdom' },
  { code: 'US', flag: '🇺🇸', name: 'United States' }
]

// Get display name for region
function getRegionName(region) {
  if (region.nameKey) {
    return t(region.nameKey)
  }
  return region.name
}

// Filter and sort regions based on search query
const filteredRegions = computed(() => {
  const query = searchQuery.value.toLowerCase().trim()
  if (!query) return regions

  return regions.filter(region => {
    const name = getRegionName(region).toLowerCase()
    const code = region.code.toLowerCase()
    return name.includes(query) || code.includes(query)
  })
})

const currentRegionLabel = computed(() => {
  const region = regions.find(r => r.code === selectedRegion.value)
  if (!region) return t('common.global')
  return getRegionName(region)
})

// Clear search when dropdown closes
watch(isOpen, (newVal) => {
  if (!newVal) {
    searchQuery.value = ''
  }
})

function updateDropdownPosition() {
  if (!buttonRef.value) return

  const rect = buttonRef.value.getBoundingClientRect()
  const menuWidth = 224 // w-56 = 14rem = 224px

  // Position below button, aligned to right edge
  dropdownStyle.value = {
    top: `${rect.bottom + 8}px`,
    left: `${rect.right - menuWidth}px`
  }
}

async function toggleDropdown() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    await nextTick()
    updateDropdownPosition()
    // Focus search input
    searchInputRef.value?.focus()
  }
}

function selectRegion(code) {
  selectedRegion.value = code
  if (code) {
    localStorage.setItem(STORAGE_KEY, code)
  } else {
    localStorage.removeItem(STORAGE_KEY)
  }
  isOpen.value = false
  // Trigger a page refresh to reload marketplace with new region filter
  window.dispatchEvent(new CustomEvent('region-changed', { detail: { region: code } }))
}

function handleClickOutside(event) {
  // Check if click is outside both the button and the menu
  const isOutsideButton = dropdownRef.value && !dropdownRef.value.contains(event.target)
  const isOutsideMenu = menuRef.value && !menuRef.value.contains(event.target)

  if (isOutsideButton && (isOutsideMenu || !menuRef.value)) {
    isOpen.value = false
  }
}

onMounted(() => {
  // Load saved region from localStorage
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    selectedRegion.value = saved
  }
  document.addEventListener('click', handleClickOutside)
  window.addEventListener('scroll', updateDropdownPosition, true)
  window.addEventListener('resize', updateDropdownPosition)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  window.removeEventListener('scroll', updateDropdownPosition, true)
  window.removeEventListener('resize', updateDropdownPosition)
})
</script>

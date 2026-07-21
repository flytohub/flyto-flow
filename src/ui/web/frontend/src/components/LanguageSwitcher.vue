<template>
  <div class="lang-switcher" ref="switcherRef">
    <!-- Trigger Button -->
    <button
      @click="toggleDropdown($event)"
      class="lang-trigger"
      :class="{ open: isOpen }"
      :aria-expanded="isOpen"
      aria-haspopup="listbox"
      aria-label="Change language"
    >
      <img v-if="currentFlagUrl && !currentFlagFailed" :src="currentFlagUrl" class="lang-flag" alt="" width="20" height="20" @error="currentFlagFailed = true" />
      <span v-else class="lang-flag-fallback">🌐</span>
      <ChevronDown :size="12" class="lang-arrow" :class="{ rotated: isOpen }" />
    </button>

    <!-- Dropdown Menu -->
    <Transition name="dropdown">
      <div v-if="isOpen" class="lang-dropdown" role="listbox">
        <!-- Search Input -->
        <div class="search-wrapper">
          <Search :size="14" class="search-icon" />
          <AppInput
            ref="searchInput"
            v-model="searchQuery"
            :placeholder="$t('common.search') || 'Search...'"
            @click.stop
          />
        </div>

        <!-- Language List -->
        <div class="lang-list">
          <button
            v-for="lang in filteredLanguages"
            :key="lang.code"
            @click="selectLanguage(lang.code, $event)"
            class="lang-option"
            :class="{ active: currentLocale === lang.code }"
            role="option"
            :aria-selected="currentLocale === lang.code"
          >
            <img v-if="lang.flagUrl && !failedFlags.has(lang.code)" :src="lang.flagUrl" class="option-flag" alt="" width="20" height="20" @error="markFlagFailed(lang.code)" />
            <span v-else class="option-flag-fallback">🌐</span>
            <div class="option-text">
              <span class="option-native">{{ lang.displayName }}</span>
              <span class="option-name">{{ lang.name }}</span>
            </div>
            <Check v-if="currentLocale === lang.code" :size="14" class="check-icon" />
          </button>

          <!-- No Results -->
          <div v-if="filteredLanguages.length === 0" class="no-results">
            {{ $t('common.noOptions') || 'No languages found' }}
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { ChevronDown, Search, Check } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import { setLocale, getLocale, getAvailableLocales } from '@/i18n'
import { useUserStore } from '@/stores/userStore'
import { telemetry } from '@/services/telemetry'
import { regionToFlag, localeToFlag, regionToFlagUrl, localeToFlagUrl } from '@/utils/emoji'

const userStore = useUserStore()
const currentLocale = ref(getLocale())
const isOpen = ref(false)
const switcherRef = ref(null)
const searchInput = ref(null)
const searchQuery = ref('')
// Track flag URLs that 404'd so we can swap to the globe fallback
// without leaving a broken-image icon in the dropdown.
const currentFlagFailed = ref(false)
const failedFlags = ref(new Set())

function markFlagFailed(code) {
  const next = new Set(failedFlags.value)
  next.add(code)
  failedFlags.value = next
}

// Hardcoded locale metadata as ultimate fallback
const LOCALE_METADATA = {
  en: { name: 'English', native: 'English', region: 'US' },
  'zh-TW': { name: 'Traditional Chinese', native: '繁體中文', region: 'TW' },
  'zh-CN': { name: 'Simplified Chinese', native: '简体中文', region: 'CN' },
  ja: { name: 'Japanese', native: '日本語', region: 'JP' },
  ko: { name: 'Korean', native: '한국어', region: 'KR' },
  fr: { name: 'French', native: 'Français', region: 'FR' },
  es: { name: 'Spanish', native: 'Español', region: 'ES' },
  hi: { name: 'Hindi', native: 'हिन्दी', region: 'IN' }
}

/**
 * Get circle-flag SVG URL for a locale (works on all platforms including Windows).
 * Falls back to emoji globe only when no SVG is available.
 */
function getFlagUrlForLocale(lang) {
  if (lang.region && lang.region.length === 2) {
    const url = regionToFlagUrl(lang.region)
    if (url) return url
  }
  const meta = LOCALE_METADATA[lang.code]
  if (meta?.region) {
    const url = regionToFlagUrl(meta.region)
    if (url) return url
  }
  return localeToFlagUrl(lang.code)
}

/**
 * Get display name for a locale with fallbacks
 */
function getDisplayName(lang) {
  // Priority: native > name > hardcoded > code
  if (lang.native && lang.native !== lang.code) return lang.native
  if (lang.name && lang.name !== lang.code) return lang.name

  const meta = LOCALE_METADATA[lang.code]
  if (meta?.native) return meta.native

  return lang.code
}

const languages = computed(() => {
  const locales = getAvailableLocales()

  // Get allowed languages from store (with safety check)
  let allowed
  let isAdmin = false
  let isAuthenticated = false
  try {
    allowed = userStore.allowedLanguages
    isAdmin = userStore.isAdmin
    isAuthenticated = userStore.isAuthenticated
  } catch {
    allowed = null
  }

  return locales
    .filter(lang => {
      // Always show all languages for:
      // 1. Admin users (null = all allowed)
      // 2. Not authenticated users (let them choose before login)
      // 3. Store not ready (fallback)
      if (allowed === null || isAdmin || !isAuthenticated) return true
      // Otherwise filter by allowed_languages
      return allowed.includes(lang.code)
    })
    .map(lang => ({
      ...lang,
      flagUrl: getFlagUrlForLocale(lang),
      displayName: getDisplayName(lang),
      name: lang.name || LOCALE_METADATA[lang.code]?.name || lang.code
    }))
    .sort((a, b) => a.displayName.localeCompare(b.displayName))
})

const filteredLanguages = computed(() => {
  if (!searchQuery.value.trim()) {
    return languages.value
  }

  const query = searchQuery.value.toLowerCase().trim()
  return languages.value.filter(lang =>
    lang.displayName.toLowerCase().includes(query) ||
    lang.name.toLowerCase().includes(query) ||
    lang.code.toLowerCase().includes(query)
  )
})

const currentFlagUrl = computed(() => {
  const lang = languages.value.find(l => l.code === currentLocale.value)
  return lang?.flagUrl || null
})

// When CDN manifest finishes loading the trigger flag URL changes (e.g.
// because the metadata gained a region). Reset the failure flag so the
// fresh URL is given a chance to load.
watch(currentFlagUrl, () => {
  currentFlagFailed.value = false
})

function toggleDropdown(event) {
  event.stopPropagation()
  isOpen.value = !isOpen.value
}

// Focus search input when dropdown opens
watch(isOpen, (open) => {
  if (open) {
    searchQuery.value = ''
    nextTick(() => {
      searchInput.value?.focus()
    })
  }
})

async function selectLanguage(code, event) {
  event.stopPropagation()

  if (code === currentLocale.value) {
    isOpen.value = false
    return
  }

  const oldLocale = currentLocale.value
  currentLocale.value = code

  // Track language change
  telemetry.track('settings.language_change', {
    old_lang: oldLocale,
    new_lang: code
  })

  await setLocale(code)
  isOpen.value = false
  window.location.reload()
}

function handleClickOutside(event) {
  // Ensure we're not clicking on the switcher itself
  if (switcherRef.value && !switcherRef.value.contains(event.target)) {
    isOpen.value = false
  }
}

onMounted(() => {
  // Use mousedown for more reliable outside-click detection
  document.addEventListener('mousedown', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside)
})
</script>

<style scoped>
.lang-switcher {
  position: relative;
}

.lang-trigger {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #e2e8f0;
  cursor: pointer;
  transition: all 0.2s;
}

.lang-trigger:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.lang-trigger.open {
  background: rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.4);
}

.lang-flag {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  object-fit: cover;
}

.lang-flag-fallback {
  font-size: 18px;
  line-height: 1;
}

.lang-arrow {
  color: #94a3b8;
  transition: transform 0.2s;
}

.lang-arrow.rotated {
  transform: rotate(180deg);
}

.lang-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  width: 260px;
  background: #1e293b;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  overflow: hidden;
  z-index: 1000;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}

/* Search */
.search-wrapper {
  position: relative;
  padding: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.search-icon {
  position: absolute;
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
  color: #64748b;
  pointer-events: none;
  z-index: 1;
}

.search-wrapper :deep(input) {
  padding-left: 32px !important;
}

/* Language List */
.lang-list {
  max-height: 280px;
  overflow-y: auto;
  padding: 6px;
}

.lang-list::-webkit-scrollbar {
  width: 6px;
}

.lang-list::-webkit-scrollbar-track {
  background: transparent;
}

.lang-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.lang-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

.lang-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: #cbd5e1;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
}

.lang-option:hover {
  background: rgba(255, 255, 255, 0.06);
}

.lang-option.active {
  background: rgba(139, 92, 246, 0.15);
  color: #e2e8f0;
}

.option-flag {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.option-flag-fallback {
  font-size: 20px;
  line-height: 1;
  flex-shrink: 0;
}

.option-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.option-native {
  font-weight: 500;
  color: #f1f5f9;
}

.option-name {
  font-size: 11px;
  color: #64748b;
}

.check-icon {
  color: #a78bfa;
  flex-shrink: 0;
}

.no-results {
  padding: 20px;
  text-align: center;
  color: #64748b;
  font-size: 13px;
}

/* Dropdown Transition */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease-out;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>

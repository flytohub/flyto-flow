<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Header -->
    <div class="bg-gradient-to-r from-gray-800 to-gray-900 border-b border-gray-700">
      <div class="container mx-auto px-4 py-6">
        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 class="text-2xl font-bold text-white flex items-center gap-2">
              <Activity :size="24" class="text-purple-400" />
              {{ $t('observability.title', 'Observability') }}
            </h1>
            <p class="text-gray-400 mt-1">{{ $t('observability.subtitle', 'Monitor workflow executions and performance') }}</p>
          </div>

          <!-- Time Range Selector -->
          <div class="flex items-center gap-3">
            <div class="relative" ref="timeRangeRef">
              <button
                @click="timeRangeOpen = !timeRangeOpen"
                class="flex items-center gap-2 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm hover:border-gray-500 transition-colors"
                :aria-expanded="timeRangeOpen"
                aria-haspopup="listbox"
              >
                <Clock :size="14" class="text-gray-400" />
                <span>{{ timeRangeOptions.find(o => o.value === timeRange)?.label }}</span>
                <ChevronDown :size="14" class="text-gray-400 transition-transform" :class="{ 'rotate-180': timeRangeOpen }" />
              </button>
              <Transition name="dropdown">
                <div v-if="timeRangeOpen" class="absolute right-0 top-full mt-1.5 w-48 bg-gray-800 border border-gray-700 rounded-lg shadow-lg shadow-black/30 z-50 py-1 overflow-hidden" role="listbox">
                  <button
                    v-for="opt in timeRangeOptions"
                    :key="opt.value"
                    @click="timeRange = opt.value; timeRangeOpen = false; handleTimeRangeChange()"
                    class="flex items-center justify-between w-full px-3 py-2 text-sm text-left transition-colors"
                    :class="timeRange === opt.value
                      ? 'bg-purple-900/30 text-purple-400'
                      : 'text-gray-300 hover:bg-gray-700/50'"
                    role="option"
                    :aria-selected="timeRange === opt.value"
                  >
                    {{ opt.label }}
                    <Check v-if="timeRange === opt.value" :size="14" class="text-purple-400" />
                  </button>
                </div>
              </Transition>
            </div>

            <button
              @click="refreshData"
              :disabled="isRefreshing"
              class="p-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCw :size="18" :class="{ 'animate-spin': isRefreshing }" />
            </button>
          </div>
        </div>

        <!-- Tab Navigation -->
        <div class="flex items-center gap-1 mt-6 -mb-px">
          <router-link
            v-for="tab in tabs"
            :key="tab.path"
            :to="tab.path"
            class="px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors flex items-center gap-2"
            :class="[
              isActiveTab(tab.path)
                ? 'bg-gray-900 text-white border-t border-l border-r border-gray-700'
                : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
            ]"
          >
            <component :is="tab.icon" :size="16" />
            {{ tab.label }}
          </router-link>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="bg-gray-900 min-h-[calc(100vh-200px)]">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" :time-range="timeRange" />
        </transition>
      </router-view>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Activity, BarChart3, Workflow, Bell, RefreshCw, Clock, ChevronDown, Check } from 'lucide-vue-next'
import { DEFAULTS } from '@/config/defaults'

const { t } = useI18n()
const route = useRoute()

// State
const timeRange = ref('7d')
const isRefreshing = ref(false)
const timeRangeOpen = ref(false)
const timeRangeRef = ref(null)

const timeRangeOptions = computed(() => [
  { value: '24h', label: t('observability.timeRange.24h', 'Last 24 hours') },
  { value: '7d', label: t('observability.timeRange.7d', 'Last 7 days') },
  { value: '30d', label: t('observability.timeRange.30d', 'Last 30 days') },
  { value: '90d', label: t('observability.timeRange.90d', 'Last 90 days') },
])

// Tabs configuration
const tabs = computed(() => [
  {
    path: '/observability/metrics',
    label: t('observability.tabs.metrics', 'Metrics'),
    icon: BarChart3
  },
  {
    path: '/observability/traces',
    label: t('observability.tabs.traces', 'Traces'),
    icon: Workflow
  },
  {
    path: '/observability/alerts',
    label: t('observability.tabs.alerts', 'Alerts'),
    icon: Bell
  }
])

// Check if tab is active
function isActiveTab(path) {
  return route.path === path || route.path.startsWith(path + '/')
}

// Click outside handler
function handleClickOutside(e) {
  if (timeRangeRef.value && !timeRangeRef.value.contains(e.target)) {
    timeRangeOpen.value = false
  }
}

onMounted(() => document.addEventListener('mousedown', handleClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', handleClickOutside))

// Handle time range change
function handleTimeRangeChange() {
  refreshData()
}

// Refresh data
async function refreshData() {
  isRefreshing.value = true
  // The child components will handle their own refresh via props or store
  await new Promise(resolve => setTimeout(resolve, DEFAULTS.TIMING.ANIMATION_STAGGER))
  isRefreshing.value = false
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s ease-out;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>

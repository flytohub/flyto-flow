<template>
  <ErrorBoundary @error="handleGlobalError">
    <div id="app" class="flex flex-col min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <AppNavbar v-if="!isFullscreenPage" />
      <BrowserEngineBanner v-if="!isFullscreenPage" />
      <main :class="isFullscreenPage ? 'h-screen' : 'flex-1'">
        <PageTransition />
      </main>
      <ToastContainer />
      <GlobalConfirmDialog />
      <AppFooter v-if="!isFullscreenPage" />
      <GlobalInteractOverlay />
      <PluginUIOverlay />
    </div>
  </ErrorBoundary>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppNavbar from './components/layout/AppNavbar.vue'
import AppFooter from './components/layout/AppFooter.vue'
import BrowserEngineBanner from './components/layout/BrowserEngineBanner.vue'
import ToastContainer from './components/common/ToastContainer.vue'
import GlobalConfirmDialog from './components/common/GlobalConfirmDialog.vue'
import PageTransition from './components/common/PageTransition.vue'
import ErrorBoundary from './components/common/ErrorBoundary.vue'
import GlobalInteractOverlay from './components/execution/GlobalInteractOverlay.vue'
import PluginUIOverlay from './components/execution/PluginUIOverlay.vue'
import { useUserStore } from './stores/userStore'
import { useConfigStore } from './stores/configStore'
import { useDarkMode } from './composables/useDarkMode'
import { useBreakpointWS } from './composables/useBreakpointWS'

const route = useRoute()
const userStore = useUserStore()
const configStore = useConfigStore()

useDarkMode()
useBreakpointWS()

const isFullscreenPage = computed(() => (
  route.path === '/login' || route.path.startsWith('/templates/builder')
))

onMounted(async () => {
  await Promise.allSettled([configStore.loadConfig(), userStore.init()])
})

function handleGlobalError({ error, info }) {
  console.error('Global error caught:', error, info)
}
</script>

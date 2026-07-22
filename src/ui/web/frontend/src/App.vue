<template>
  <ErrorBoundary @error="handleGlobalError">
    <div id="app" class="flex min-h-screen flex-col bg-white text-gray-900 dark:bg-gray-900 dark:text-gray-100">
      <AppNavbar v-if="!isFullscreenPage">
        <template #navigation>
          <component :is="NavigationExtension" v-if="NavigationExtension" />
        </template>
        <template #actions>
          <component :is="HeaderActionsExtension" v-if="HeaderActionsExtension" />
        </template>
      </AppNavbar>
      <component :is="AppBanner" v-if="AppBanner && !isFullscreenPage" />
      <main :class="isFullscreenPage ? 'h-screen' : 'flex-1'">
        <PageTransition />
      </main>
      <ToastContainer />
      <GlobalConfirmDialog />
      <AppFooter v-if="!isFullscreenPage">
        <component :is="FooterContentExtension" v-if="FooterContentExtension" />
      </AppFooter>
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
import ToastContainer from './components/common/ToastContainer.vue'
import GlobalConfirmDialog from './components/common/GlobalConfirmDialog.vue'
import PageTransition from './components/common/PageTransition.vue'
import ErrorBoundary from './components/common/ErrorBoundary.vue'
import GlobalInteractOverlay from './components/execution/GlobalInteractOverlay.vue'
import PluginUIOverlay from './components/execution/PluginUIOverlay.vue'
import { useConfigStore } from './stores/configStore'
import { useDarkMode } from './composables/useDarkMode'
import { useBreakpointWS } from './composables/useBreakpointWS'
import {
  AppBanner,
  FooterContentExtension,
  HeaderActionsExtension,
  NavigationExtension,
} from '@edition'

const route = useRoute()
const configStore = useConfigStore()
useDarkMode()
useBreakpointWS()

const isFullscreenPage = computed(() => route.path.startsWith('/templates/builder'))

onMounted(() => configStore.loadConfig())

function handleGlobalError({ error, info }) {
  console.error('Global error caught:', error, info)
}
</script>

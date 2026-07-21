<template>
  <footer class="bg-gray-900 text-white">
    <div class="container mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      <div class="flex flex-col md:flex-row justify-between items-center gap-6">
        <!-- Brand Section -->
        <div class="flex flex-col items-center md:items-start gap-4">
          <div class="flex items-center gap-3">
            <img src="/logo.png" alt="Flyto2" class="h-10 w-auto" />
          </div>
          <p class="text-gray-400 text-sm leading-relaxed max-w-md text-center md:text-left">
            {{ $t('footer.description') }}
          </p>
        </div>

        <!-- Social Links -->
        <div class="flex items-center gap-3">
          <a href="https://www.facebook.com/profile.php?id=61588289642274" target="_blank" rel="noopener noreferrer" class="w-10 h-10 bg-gray-800 hover:bg-blue-600 rounded-lg flex items-center justify-center transition-colors">
            <Facebook :size="22" />
          </a>
          <a href="https://www.youtube.com/@Flyto2" target="_blank" rel="noopener noreferrer" class="w-10 h-10 bg-gray-800 hover:bg-red-600 rounded-lg flex items-center justify-center transition-colors">
            <Youtube :size="22" />
          </a>
          <a :href="githubUrl" target="_blank" rel="noopener noreferrer" class="w-10 h-10 bg-gray-800 hover:bg-primary-600 rounded-lg flex items-center justify-center transition-colors">
            <Github :size="22" />
          </a>
        </div>
      </div>

      <!-- Footer Bottom -->
      <div class="mt-8 pt-6 border-t border-gray-800 space-y-2">
        <p class="text-sm text-gray-400 text-center">
          {{ $t('footer.copyright', { year: currentYear }) }}
        </p>
        <p class="text-xs text-gray-500 text-center max-w-2xl mx-auto leading-relaxed">
          {{ $t('footer.disclaimer') }}
        </p>
        <p v-if="isDesktop && (appVersion || coreVersion)" class="text-xs text-gray-600 text-right">
          <span v-if="appVersion">v{{ appVersion }}</span>
          <span v-if="appVersion && coreVersion"> · </span>
          <span v-if="coreVersion">core v{{ coreVersion }}</span>
        </p>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { Facebook, Github, Youtube } from 'lucide-vue-next'
import { EXTERNAL_URLS } from '@/config/urls'
import { API_URL } from '@/api/config'
import { trackApp } from '@/utils/telemetry/appTracker'

const githubUrl = EXTERNAL_URLS.GITHUB_REPO
const currentYear = computed(() => new Date().getFullYear())
const isDesktop = ref(false)
const appVersion = ref('')
const coreVersion = ref('')

onMounted(async () => {
  isDesktop.value = !!window.__TAURI_INTERNALS__
  if (!isDesktop.value) return

  const [appRes, coreRes] = await Promise.allSettled([
    fetch(`${API_URL}/app/version`),
    fetch(`${API_URL}/core/version`)
  ])
  if (appRes.status === 'fulfilled' && appRes.value.ok) {
    appVersion.value = (await appRes.value.json()).version
  }
  if (coreRes.status === 'fulfilled' && coreRes.value.ok) {
    coreVersion.value = (await coreRes.value.json()).version
  }

  trackApp.launch(appVersion.value, coreVersion.value)
})
</script>

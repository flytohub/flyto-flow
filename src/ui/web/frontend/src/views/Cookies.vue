<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 sm:py-16">
    <div class="container px-4 max-w-4xl mx-auto">
      <h1 class="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-8">{{ $t('cookies.title') }}</h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-8">{{ $t('cookies.lastUpdated') }}: 2025-12-05</p>

      <div class="prose dark:prose-invert max-w-none space-y-8">
        <section class="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 border border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $t('cookies.sections.what.title') }}</h2>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">{{ $t('cookies.sections.what.content') }}</p>
        </section>

        <section class="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 border border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $t('cookies.sections.types.title') }}</h2>
          <div class="space-y-4">
            <div>
              <h3 class="font-medium text-gray-900 dark:text-gray-100 mb-2">{{ $t('cookies.sections.types.essential.title') }}</h3>
              <p class="text-gray-600 dark:text-gray-400">{{ $t('cookies.sections.types.essential.content') }}</p>
            </div>
            <div>
              <h3 class="font-medium text-gray-900 dark:text-gray-100 mb-2">{{ $t('cookies.sections.types.functional.title') }}</h3>
              <p class="text-gray-600 dark:text-gray-400">{{ $t('cookies.sections.types.functional.content') }}</p>
            </div>
            <div>
              <h3 class="font-medium text-gray-900 dark:text-gray-100 mb-2">{{ $t('cookies.sections.types.analytics.title') }}</h3>
              <p class="text-gray-600 dark:text-gray-400">{{ $t('cookies.sections.types.analytics.content') }}</p>
            </div>
          </div>
        </section>

        <section class="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 border border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $t('cookies.sections.manage.title') }}</h2>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed mb-6">{{ $t('cookies.sections.manage.content') }}</p>

          <div class="space-y-4">
            <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div>
                <h3 class="font-medium text-gray-900 dark:text-gray-100">{{ $t('cookies.sections.types.essential.title') }}</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">{{ $t('cookies.alwaysOn') }}</p>
              </div>
              <ToggleSwitch :model-value="true" disabled />
            </div>

            <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div>
                <h3 class="font-medium text-gray-900 dark:text-gray-100">{{ $t('cookies.sections.types.functional.title') }}</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">{{ $t('cookies.optional') }}</p>
              </div>
              <ToggleSwitch v-model="functionalCookies" />
            </div>

            <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div>
                <h3 class="font-medium text-gray-900 dark:text-gray-100">{{ $t('cookies.sections.types.analytics.title') }}</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">{{ $t('cookies.optional') }}</p>
              </div>
              <ToggleSwitch v-model="analyticsCookies" />
            </div>
          </div>

          <button
            @click="saveCookiePreferences"
            class="mt-6 px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors"
          >
            {{ $t('cookies.savePreferences') }}
          </button>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useToast } from '../composables/useToast'
import { useI18n } from 'vue-i18n'
import ToggleSwitch from '../components/common/ToggleSwitch.vue'

const { t } = useI18n()
const toast = useToast()

const functionalCookies = ref(true)
const analyticsCookies = ref(false)

function saveCookiePreferences() {
  localStorage.setItem('cookie_preferences', JSON.stringify({
    functional: functionalCookies.value,
    analytics: analyticsCookies.value
  }))
  toast.success(t('cookies.preferencesSaved'))
}
</script>

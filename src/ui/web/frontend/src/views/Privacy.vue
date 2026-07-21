<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 sm:py-16">
    <div class="container px-4 max-w-4xl mx-auto">
      <h1 class="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-8">{{ $t('privacy.title') }}</h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-8">{{ $t('privacy.lastUpdated') }}: {{ legalMeta.lastUpdated }}</p>

      <div class="prose dark:prose-invert max-w-none space-y-8">
        <section class="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 border border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $t('privacy.sections.collection.title') }}</h2>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">{{ $t('privacy.sections.collection.content') }}</p>
        </section>

        <section class="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 border border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $t('privacy.sections.usage.title') }}</h2>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">{{ $t('privacy.sections.usage.content') }}</p>
        </section>

        <section class="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 border border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $t('privacy.sections.sharing.title') }}</h2>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">{{ $t('privacy.sections.sharing.content') }}</p>
        </section>

        <section class="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 border border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $t('privacy.sections.security.title') }}</h2>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">{{ $t('privacy.sections.security.content') }}</p>
        </section>

        <section class="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 border border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $t('privacy.sections.rights.title') }}</h2>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">{{ $t('privacy.sections.rights.content') }}</p>
        </section>

        <section class="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 border border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $t('privacy.sections.contact.title') }}</h2>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">{{ $t('privacy.sections.contact.content') }}</p>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { getLegalPageMetadata } from '../constants/legal'

const legalMeta = getLegalPageMetadata('privacy')
</script>

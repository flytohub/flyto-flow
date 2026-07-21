<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 sm:py-16">
    <div class="container px-4 max-w-4xl mx-auto">
      <h1 class="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-8">{{ $t('terms.title') }}</h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-8">{{ $t('terms.lastUpdated') }}: {{ legalMeta.lastUpdated }}</p>

      <div class="prose dark:prose-invert max-w-none space-y-8">
        <section class="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 border border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $t('terms.sections.acceptance.title') }}</h2>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">{{ $t('terms.sections.acceptance.content') }}</p>
        </section>

        <section class="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 border border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $t('terms.sections.services.title') }}</h2>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">{{ $t('terms.sections.services.content') }}</p>
        </section>

        <section class="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 border border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $t('terms.sections.account.title') }}</h2>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">{{ $t('terms.sections.account.content') }}</p>
        </section>

        <section class="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 border border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $t('terms.sections.prohibited.title') }}</h2>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">{{ $t('terms.sections.prohibited.content') }}</p>
        </section>

        <section class="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 border border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $t('terms.sections.intellectual.title') }}</h2>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">{{ $t('terms.sections.intellectual.content') }}</p>
        </section>

        <section class="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 border border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $t('terms.sections.limitation.title') }}</h2>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">{{ $t('terms.sections.limitation.content') }}</p>
        </section>

        <section class="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 border border-gray-200 dark:border-gray-700">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">{{ $t('terms.sections.termination.title') }}</h2>
          <p class="text-gray-600 dark:text-gray-400 leading-relaxed">{{ $t('terms.sections.termination.content') }}</p>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { getLegalPageMetadata } from '../constants/legal'

const legalMeta = getLegalPageMetadata('terms')
</script>

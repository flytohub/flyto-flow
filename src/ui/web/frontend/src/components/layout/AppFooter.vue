<template>
  <footer class="bg-gray-900 text-white">
    <div class="container mx-auto px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <div class="flex flex-col items-center justify-between gap-6 md:flex-row">
        <div class="flex flex-col items-center gap-4 md:items-start">
          <div class="flex items-center gap-3">
            <img src="/logo.png" alt="Flyto2" class="brand-logo" />
          </div>
          <p class="max-w-md text-center text-sm leading-relaxed text-gray-400 md:text-left">
            {{ $t('footer.description') }}
          </p>
        </div>
        <slot />
      </div>

      <div class="mt-8 space-y-2 border-t border-gray-800 pt-6">
        <p class="text-center text-sm text-gray-400">
          {{ $t('footer.copyright', { year: currentYear }) }}
        </p>
        <p class="mx-auto max-w-2xl text-center text-xs leading-relaxed text-gray-500">
          {{ $t('footer.disclaimer') }}
        </p>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'

const currentYear = computed(() => new Date().getFullYear())
</script>

<style scoped>
.brand-logo { height: 3.5rem; width: auto; }
</style>

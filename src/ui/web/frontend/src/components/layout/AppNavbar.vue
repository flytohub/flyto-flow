<template>
  <nav class="sticky top-0 z-50 border-b border-gray-200 bg-white/95 shadow-sm backdrop-blur-md transition-colors duration-200 dark:border-gray-700 dark:bg-gray-900/95">
    <div class="container mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex h-16 items-center justify-between sm:h-20">
        <div class="flex min-w-0 items-center gap-4">
          <router-link to="/" aria-label="Flyto2 Flow" class="group flex items-center gap-2 transition-opacity hover:opacity-80 sm:gap-3">
            <img src="/logo.png" alt="Flyto2" class="brand-logo w-auto transition-transform duration-300 group-hover:scale-105" />
          </router-link>
          <slot name="navigation" />
        </div>
        <div class="flex items-center gap-2">
          <LanguageSwitcher />
          <slot name="actions" />
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
</script>

<style scoped>
.brand-logo { height: 3.5rem; width: auto; }
</style>

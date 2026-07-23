<template>
  <nav class="app-navbar sticky top-0 z-50 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border-b border-gray-200 dark:border-gray-700 shadow-sm transition-colors duration-200">
    <div class="container mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16 sm:h-20">
        <router-link to="/" aria-label="Flyto2 Flow" class="flex items-center gap-2 sm:gap-3 hover:opacity-80 transition-opacity group">
          <img src="/logo.png" alt="Flyto2" class="h-8 sm:h-10 w-auto group-hover:scale-105 transition-transform duration-300" />
        </router-link>
        <div class="app-navbar__desktop-navigation hidden md:flex items-center gap-1 lg:gap-2" :aria-label="t('mcpStudio.primaryNavigation')">
          <router-link v-for="item in navigation" :key="item.to" :to="item.to" class="nav-link">
            <component :is="item.icon" :size="20" />
            <span>{{ item.label }}</span>
          </router-link>
          <slot name="navigation" />
        </div>
        <div class="hidden md:flex items-center gap-2">
          <LanguageSwitcher />
          <slot name="actions" />
        </div>
        <div class="flex md:hidden items-center gap-1 flex-shrink-0">
          <LanguageSwitcher />
          <button
            class="app-navbar__mobile-menu-button p-2 text-gray-700 dark:text-gray-200 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            type="button"
            :aria-expanded="menuOpen"
            :aria-label="t('mcpStudio.toggleNavigation')"
            @click="menuOpen = !menuOpen"
          >
            <X v-if="menuOpen" :size="24" />
            <Menu v-else :size="24" />
          </button>
        </div>
      </div>
      <div v-if="menuOpen" class="app-navbar__mobile-menu md:hidden py-4 border-t border-gray-200 dark:border-gray-700 space-y-1 max-h-[calc(100vh-5rem)] overflow-y-auto">
        <router-link
          v-for="item in navigation"
          :key="item.to"
          :to="item.to"
          class="mobile-nav-link"
          @click="menuOpen = false"
        >
          <component :is="item.icon" :size="20" />
          <span>{{ item.label }}</span>
        </router-link>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Activity, Cable, GitBranch, KeyRound, Menu, X } from 'lucide-vue-next'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
import '@/features/navigation/appNavbar.css'

const { t } = useI18n()
const menuOpen = ref(false)
const navigation = computed(() => [
  { to: '/my-templates', label: t('workflow.title'), icon: GitBranch },
  { to: '/mcp', label: t('mcpStudio.nav'), icon: Cable },
  { to: '/variables', label: t('variables.title'), icon: KeyRound },
  { to: '/observability', label: t('observability.title'), icon: Activity },
])
</script>

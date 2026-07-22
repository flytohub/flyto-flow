<template>
  <nav class="sticky top-0 z-50 border-b border-gray-200 bg-white/95 shadow-sm backdrop-blur-md transition-colors duration-200 dark:border-gray-700 dark:bg-gray-900/95">
    <div class="mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-8">
      <div class="flex h-16 items-center justify-between gap-3 sm:h-20">
        <div class="flex min-w-0 items-center gap-5">
          <router-link to="/" aria-label="Flyto2 Flow" class="group flex shrink-0 items-center gap-2 transition-opacity hover:opacity-80 sm:gap-3">
            <img src="/logo.png" alt="Flyto2" class="brand-logo w-auto transition-transform duration-300 group-hover:scale-105" />
          </router-link>
          <div class="hidden items-center gap-1 lg:flex" aria-label="Primary navigation">
            <router-link v-for="item in navigation" :key="item.to" :to="item.to" class="nav-link">
              <component :is="item.icon" :size="18" />
              <span>{{ item.label }}</span>
            </router-link>
            <slot name="navigation" />
          </div>
        </div>
        <div class="flex shrink-0 items-center gap-2">
          <div class="hidden sm:block"><LanguageSwitcher /></div>
          <slot name="actions" />
          <button
            class="menu-button lg:hidden"
            type="button"
            :aria-expanded="menuOpen"
            aria-label="Toggle navigation"
            @click="menuOpen = !menuOpen"
          >
            <X v-if="menuOpen" :size="21" />
            <Menu v-else :size="21" />
          </button>
        </div>
      </div>
      <div v-if="menuOpen" class="mobile-menu lg:hidden">
        <router-link
          v-for="item in navigation"
          :key="item.to"
          :to="item.to"
          class="mobile-link"
          @click="menuOpen = false"
        >
          <component :is="item.icon" :size="19" />
          <span>{{ item.label }}</span>
        </router-link>
        <div class="border-t border-gray-200 pt-3 sm:hidden dark:border-gray-700">
          <LanguageSwitcher />
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue'
import { Activity, Cable, GitBranch, KeyRound, Menu, X } from 'lucide-vue-next'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'

const menuOpen = ref(false)
const navigation = [
  { to: '/my-templates', label: 'Workflows', icon: GitBranch },
  { to: '/mcp', label: 'MCP Studio', icon: Cable },
  { to: '/variables', label: 'Variables', icon: KeyRound },
  { to: '/observability', label: 'Monitor', icon: Activity },
]
</script>

<style scoped>
.brand-logo { height: 3.5rem; width: auto; }

.nav-link,
.mobile-link,
.menu-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  border-radius: 8px;
  color: #4b5563;
  font-size: 0.875rem;
  font-weight: 600;
}

.nav-link { min-height: 2.5rem; padding: 0 0.75rem; }
.nav-link:hover,
.nav-link.router-link-active { background: #eef7f5; color: #0f766e; }
.menu-button { justify-content: center; width: 2.75rem; height: 2.75rem; border: 1px solid #d1d5db; }
.mobile-menu { padding: 0.25rem 0 1rem; }
.mobile-link { display: flex; min-height: 2.75rem; padding: 0 0.75rem; }
.mobile-link.router-link-active { background: #eef7f5; color: #0f766e; }

@media (min-width: 1024px) {
  .menu-button,
  .mobile-menu { display: none; }
}

@media (prefers-color-scheme: dark) {
  .nav-link,
  .mobile-link,
  .menu-button { color: #d1d5db; }
  .nav-link:hover,
  .nav-link.router-link-active,
  .mobile-link.router-link-active { background: #163d3a; color: #99f6e4; }
  .menu-button { border-color: #4b5563; }
}
</style>

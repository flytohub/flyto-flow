<template>
  <nav class="sticky top-0 z-50 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border-b border-gray-200 dark:border-gray-700 shadow-sm transition-colors duration-200">
    <div class="container mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16 sm:h-20">
        <!-- Logo -->
        <router-link to="/" class="flex items-center gap-2 sm:gap-3 hover:opacity-80 transition-opacity group">
          <img src="/logo.png" alt="Flyto2" class="h-8 sm:h-10 w-auto group-hover:scale-105 transition-transform duration-300" />
        </router-link>

        <!-- Desktop Menu -->
        <div class="hidden md:flex items-center gap-1 lg:gap-2">
          <router-link to="/" class="nav-link">
            <Home :size="20" />
            <span>{{ $t('common.home') }}</span>
          </router-link>
          <router-link to="/dashboard" class="nav-link">
            <LayoutDashboard :size="20" />
            <span>{{ $t('dashboard.title') }}</span>
          </router-link>
          <router-link to="/my-templates" class="nav-link">
            <GitBranch :size="20" />
            <span>{{ $t('workflow.title') }}</span>
          </router-link>
          <router-link v-if="showMarketplace" to="/marketplace" class="nav-link">
            <ShoppingBag :size="20" />
            <span>{{ $t('marketplace.title') }}</span>
          </router-link>
          <router-link v-if="isEnterprise" to="/enterprise" class="nav-link">
            <Building2 :size="20" />
            <span>{{ $t('enterprise.title', 'Enterprise') }}</span>
          </router-link>
          <!-- Tools: dropdown if Pro, single link if not -->
          <router-link v-if="!isPro" to="/plugins" class="nav-link">
            <Puzzle :size="20" />
            <span>{{ $t('plugins.title') }}</span>
          </router-link>
          <div v-else class="relative" ref="toolsMenuRef">
            <button
              @click="toolsMenuOpen = !toolsMenuOpen"
              class="nav-link flex items-center gap-1"
            >
              <Wrench :size="20" />
              <span>{{ $t('nav.tools', 'Tools') }}</span>
              <ChevronDown :size="16" :class="{ 'rotate-180': toolsMenuOpen }" class="transition-transform" />
            </button>
            <div
              v-if="toolsMenuOpen"
              class="absolute top-full left-0 mt-1 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg py-1 z-50"
            >
              <router-link to="/plugins" @click="toolsMenuOpen = false" class="dropdown-item">
                <Puzzle :size="16" />
                {{ $t('plugins.title') }}
              </router-link>
              <router-link to="/mcp" @click="toolsMenuOpen = false" class="dropdown-item">
                <Cable :size="16" />
                MCP
              </router-link>
              <router-link v-if="showObservability" to="/observability" @click="toolsMenuOpen = false" class="dropdown-item">
                <Activity :size="16" />
                {{ $t('observability.title', 'Observability') }}
              </router-link>
            </div>
          </div>
        </div>


        <!-- Right Section: Language, Dark Mode, Notifications, User/Exit -->
        <div class="hidden md:flex items-center gap-2">
          <!-- Language Switcher -->
          <LanguageSwitcher />

          <!-- Trial Badge (cloud only) -->
          <router-link
            v-if="isLoggedIn && isTrialActive"
            to="/pricing"
            class="flex items-center gap-1.5 px-2.5 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-lg text-xs font-medium hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors"
          >
            <Clock :size="14" />
            <span>{{ $t('cloudTrial.navBadge', { days: trialDaysRemaining }) }}</span>
          </router-link>

          <!-- Triggers Indicator -->
          <TriggersIndicator v-if="isLoggedIn && !authLoading" />

          <!-- Notification Center -->
          <NotificationCenter v-if="isLoggedIn && !authLoading" />

          <!-- User Dropdown Menu -->
          <div v-if="isLoggedIn" class="relative">
            <button
              @click="userMenuOpen = !userMenuOpen"
              data-testid="user-menu-btn"
              class="flex items-center gap-2 px-3 py-2 bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 rounded-lg font-semibold text-sm hover:bg-primary-100 dark:hover:bg-primary-900/50 transition-colors"
            >
              <User :size="18" />
              <span>{{ username }}</span>
              <ChevronDown :size="16" :class="userMenuOpen ? 'rotate-180' : ''" class="transition-transform" />
            </button>

            <!-- User Dropdown -->
            <div
              v-if="userMenuOpen"
              class="absolute right-0 top-full mt-2 w-56 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 py-2 z-50"
            >
              <!-- User Info -->
              <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                <p class="text-sm font-semibold text-gray-900 dark:text-gray-100">{{ username }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ userEmail }}</p>
                <span v-if="isAdmin" class="inline-flex items-center gap-1 mt-1 px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 text-xs font-medium rounded-full">
                  <Shield :size="12" />
                  {{ $t('admin.users.roles.admin') }}
                </span>
              </div>

              <!-- Product Switcher -->
              <div class="py-1 border-b border-gray-200 dark:border-gray-700">
                <p class="px-4 py-1 text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">Switch Product</p>
                <a
                  href="#"
                  class="flex items-center gap-3 px-4 py-2 text-sm text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/20 font-medium"
                >
                  <Zap :size="16" />
                  Flyto2 Automation
                  <Check :size="14" class="ml-auto" />
                </a>
                <!-- TODO: Cortex — hidden until tested; re-enable when ready -->
                <!-- <a
                  :href="cortexUrl"
                  @click.prevent="switchToCortex"
                  class="flex items-center gap-3 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  <Brain :size="16" />
                  Flyto2 Cortex
                </a> -->
              </div>

              <!-- Account -->
              <div class="py-1">
                <router-link
                  v-if="userId"
                  :to="`/creators/${userId}`"
                  @click="userMenuOpen = false"
                  class="menu-item"
                >
                  <User :size="16" />
                  {{ $t('userSettings.myProfile') }}
                </router-link>
                <router-link
                  to="/settings"
                  @click="userMenuOpen = false"
                  class="menu-item"
                >
                  <Settings :size="16" />
                  {{ $t('userSettings.title') }}
                </router-link>
                <router-link
                  to="/variables"
                  @click="userMenuOpen = false"
                  class="menu-item"
                >
                  <Key :size="16" />
                  {{ $t('variables.title') }}
                </router-link>
                <router-link
                  to="/messages"
                  @click="userMenuOpen = false"
                  class="menu-item"
                >
                  <div class="relative">
                    <MessageSquare :size="16" />
                    <span
                      v-if="unreadCount > 0"
                      class="absolute -top-1.5 -right-1.5 min-w-[16px] h-4 px-1 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center"
                    >
                      {{ unreadCount > 99 ? '99+' : unreadCount }}
                    </span>
                  </div>
                  {{ $t('chat.messages') }}
                </router-link>
                <router-link
                  to="/issues"
                  @click="userMenuOpen = false"
                  class="menu-item"
                >
                  <CircleDot :size="16" />
                  {{ $t('issues.title', 'Issues') }}
                </router-link>
              </div>

              <!-- Billing & Marketplace -->
              <div v-if="showMarketplace || showSubscriptions" class="py-1 border-t border-gray-200 dark:border-gray-700">
                <router-link
                  v-if="showMarketplace"
                  to="/creator"
                  @click="userMenuOpen = false"
                  class="menu-item"
                >
                  <BarChart3 :size="16" />
                  {{ $t('creator.dashboard.title', 'Creator Dashboard') }}
                </router-link>
                <router-link
                  v-if="showMarketplace"
                  to="/purchases"
                  @click="userMenuOpen = false"
                  class="menu-item"
                >
                  <Receipt :size="16" />
                  {{ $t('purchases.title', 'Purchases') }}
                </router-link>
                <router-link
                  v-if="showSubscriptions"
                  to="/subscription"
                  @click="userMenuOpen = false"
                  class="menu-item"
                >
                  <Crown :size="16" />
                  {{ $t('subscriptions.title') }}
                </router-link>
                <router-link
                  v-if="showMarketplace"
                  to="/settings/payout"
                  @click="userMenuOpen = false"
                  class="menu-item"
                >
                  <Wallet :size="16" />
                  {{ $t('payoutSettings.title') }}
                </router-link>
              </div>

              <!-- Organization -->
              <div v-if="showOrgSettings || showRbacSettings" class="py-1 border-t border-gray-200 dark:border-gray-700">
                <router-link
                  v-if="showOrgSettings"
                  to="/settings/organization"
                  @click="userMenuOpen = false"
                  class="menu-item"
                >
                  <Building2 :size="16" />
                  {{ $t('organization.title', 'Organization') }}
                </router-link>
                <router-link
                  v-if="showOrgSettings"
                  to="/settings/projects"
                  @click="userMenuOpen = false"
                  class="menu-item"
                >
                  <FolderKanban :size="16" />
                  {{ $t('projects.title', 'Projects') }}
                </router-link>
                <router-link
                  v-if="showRbacSettings"
                  to="/settings/roles"
                  @click="userMenuOpen = false"
                  class="menu-item"
                >
                  <ShieldCheck :size="16" />
                  {{ $t('roles.title', 'Roles & Permissions') }}
                </router-link>
              </div>

              <!-- Admin moved to the flyto-admin app — no admin routes exist in this
                   build, so the former /admin/* links were removed (they only got
                   silently redirected to / by the router guard). -->

              <!-- Logout -->
              <div class="py-1 border-t border-gray-200 dark:border-gray-700">
                <button
                  @click="handleLogout"
                  data-testid="logout-btn"
                  class="flex items-center gap-3 w-full px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  <LogOut :size="16" />
                  {{ $t('auth.logout') }}
                </button>
              </div>
            </div>
          </div>

          <!-- Login Button (hide while auth is loading) -->
          <router-link
            v-if="!isLoggedIn && !authLoading"
            to="/login"
            class="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary-600 to-purple-600 text-white font-semibold rounded-lg hover:shadow-lg transition-all"
          >
            <LogIn :size="18" />
            <span>{{ $t('auth.login') }}</span>
          </router-link>
        </div>

        <!-- Mobile Section -->
        <div class="flex md:hidden items-center gap-1 flex-shrink-0">
          <!-- Language Switcher (Mobile) -->
          <LanguageSwitcher />

          <!-- Mobile Menu Button (Hamburger) -->
          <button
            @click="mobileMenuOpen = !mobileMenuOpen"
            class="p-2 text-gray-700 dark:text-gray-200 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            :aria-label="mobileMenuOpen ? $t('accessibility.closeMenu') : $t('accessibility.openMenu')"
          >
            <Menu v-if="!mobileMenuOpen" :size="24" />
            <X v-else :size="24" />
          </button>
        </div>
      </div>

      <!-- Mobile Menu -->
      <div v-if="mobileMenuOpen" class="md:hidden py-4 border-t border-gray-200 dark:border-gray-700 space-y-1 max-h-[calc(100vh-5rem)] overflow-y-auto">
        <!-- User Info (if logged in) -->
        <div v-if="isLoggedIn" class="flex items-center gap-2 px-4 py-3 mb-2 bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 rounded-lg font-semibold">
          <User :size="20" />
          <span class="truncate">{{ username }}</span>
          <span v-if="isAdmin" class="ml-auto inline-flex items-center gap-1 px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 text-xs font-medium rounded-full flex-shrink-0">
            <Shield :size="12" />
            {{ $t('admin.users.roles.admin') }}
          </span>
        </div>

        <!-- Main Navigation Links -->
        <router-link to="/" @click="mobileMenuOpen = false" class="mobile-nav-link">
          <Home :size="20" />
          <span>{{ $t('common.home') }}</span>
        </router-link>
        <router-link to="/dashboard" @click="mobileMenuOpen = false" class="mobile-nav-link">
          <LayoutDashboard :size="20" />
          <span>{{ $t('dashboard.title') }}</span>
        </router-link>
        <router-link to="/my-templates" @click="mobileMenuOpen = false" class="mobile-nav-link">
          <GitBranch :size="20" />
          <span>{{ $t('workflow.title') }}</span>
        </router-link>
        <router-link v-if="showMarketplace" to="/marketplace" @click="mobileMenuOpen = false" class="mobile-nav-link">
          <ShoppingBag :size="20" />
          <span>{{ $t('marketplace.title') }}</span>
        </router-link>
        <router-link to="/plugins" @click="mobileMenuOpen = false" class="mobile-nav-link">
          <Puzzle :size="20" />
          <span>{{ $t('plugins.title') }}</span>
        </router-link>
        <router-link to="/mcp" @click="mobileMenuOpen = false" class="mobile-nav-link">
          <Cable :size="20" />
          <span>MCP</span>
        </router-link>
        <router-link v-if="showObservability" to="/observability" @click="mobileMenuOpen = false" class="mobile-nav-link">
          <Activity :size="20" />
          <span>{{ $t('observability.title', 'Observability') }}</span>
        </router-link>

        <!-- User Section (Mobile) -->
        <div v-if="isLoggedIn" class="border-t border-gray-200 dark:border-gray-700 pt-2 mt-2">
          <router-link to="/triggers" @click="mobileMenuOpen = false" class="mobile-nav-link">
            <Clock :size="20" />
            <span>{{ $t('triggers.indicator.title') }}</span>
          </router-link>
          <router-link v-if="userId" :to="`/creators/${userId}`" @click="mobileMenuOpen = false" class="mobile-nav-link">
            <User :size="20" />
            <span>{{ $t('userSettings.myProfile') }}</span>
          </router-link>
          <router-link v-if="showMarketplace" to="/creator" @click="mobileMenuOpen = false" class="mobile-nav-link">
            <BarChart3 :size="20" />
            <span>{{ $t('creator.dashboard.title', 'Creator Dashboard') }}</span>
          </router-link>
          <router-link to="/settings" @click="mobileMenuOpen = false" class="mobile-nav-link">
            <Settings :size="20" />
            <span>{{ $t('userSettings.title') }}</span>
          </router-link>
          <router-link to="/variables" @click="mobileMenuOpen = false" class="mobile-nav-link">
            <Key :size="20" />
            <span>{{ $t('variables.title') }}</span>
          </router-link>
          <router-link v-if="showMarketplace" to="/settings/payout" @click="mobileMenuOpen = false" class="mobile-nav-link">
            <Wallet :size="20" />
            <span>{{ $t('payoutSettings.title') }}</span>
          </router-link>
          <router-link v-if="showMarketplace" to="/purchases" @click="mobileMenuOpen = false" class="mobile-nav-link">
            <Receipt :size="20" />
            <span>{{ $t('purchases.title', 'Purchases') }}</span>
          </router-link>
          <router-link v-if="showSubscriptions" to="/subscription" @click="mobileMenuOpen = false" class="mobile-nav-link">
            <Crown :size="20" />
            <span>{{ $t('subscriptions.title') }}</span>
          </router-link>
          <router-link v-if="showOrgSettings" to="/settings/organization" @click="mobileMenuOpen = false" class="mobile-nav-link">
            <Building2 :size="20" />
            <span>{{ $t('organization.title', 'Organization') }}</span>
          </router-link>
          <router-link v-if="showOrgSettings" to="/settings/projects" @click="mobileMenuOpen = false" class="mobile-nav-link">
            <FolderKanban :size="20" />
            <span>{{ $t('projects.title', 'Projects') }}</span>
          </router-link>
          <router-link v-if="showRbacSettings" to="/settings/roles" @click="mobileMenuOpen = false" class="mobile-nav-link">
            <ShieldCheck :size="20" />
            <span>{{ $t('roles.title', 'Roles & Permissions') }}</span>
          </router-link>
          <router-link to="/messages" @click="mobileMenuOpen = false" class="mobile-nav-link">
            <div class="relative">
              <MessageSquare :size="20" />
              <span
                v-if="unreadCount > 0"
                class="absolute -top-1.5 -right-1.5 min-w-[16px] h-4 px-1 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center"
              >
                {{ unreadCount > 99 ? '99+' : unreadCount }}
              </span>
            </div>
            <span>{{ $t('chat.messages') }}</span>
          </router-link>
        </div>

        <!-- Admin links (mobile) removed — admin lives in the flyto-admin app. -->

        <!-- Login/Logout -->
        <div class="border-t border-gray-200 dark:border-gray-700 pt-2 mt-2">
          <router-link v-if="!isLoggedIn && !authLoading" to="/login" @click="mobileMenuOpen = false" class="mobile-nav-link text-primary-600 dark:text-primary-400 font-semibold">
            <LogIn :size="20" />
            <span>{{ $t('auth.login') }}</span>
          </router-link>
          <button v-if="isLoggedIn" @click="handleLogout" data-testid="logout-btn-mobile" class="mobile-nav-link w-full text-red-600 dark:text-red-400 font-semibold">
            <LogOut :size="20" />
            <span>{{ $t('auth.logout') }}</span>
          </button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Home, ShoppingBag, User, LogIn, LogOut, GitBranch, LayoutDashboard,
  Menu, X, ChevronDown, Shield, Settings, Puzzle,
  MessageSquare, Wallet, Activity, Building2, FolderKanban, ShieldCheck,
  ScrollText, Wrench, Key, Crown, Inbox, Clock, BarChart3, Receipt,
  CircleDot, Coins, Zap, Brain, Check, Cable
} from 'lucide-vue-next'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
import NotificationCenter from '@/components/notifications/NotificationCenter.vue'
import TriggersIndicator from '@/components/triggers/TriggersIndicator.vue'
import { useUserStore } from '@/stores/userStore'
import { useCapabilitiesStore } from '@/stores/capabilitiesStore'
import { useWalletStore } from '@/stores/walletStore'
import { get } from '@/api/client'
import { authAPI } from '@/api/auth'
import { ENDPOINTS } from '@/api/config'
import { DEFAULTS } from '@/config/defaults'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const capabilitiesStore = useCapabilitiesStore()
const walletStore = useWalletStore()

const walletBalance = computed(() => {
  const b = walletStore.balance
  if (b >= 10000) return `${(b / 1000).toFixed(0)}k`
  return b.toLocaleString()
})

// State
const mobileMenuOpen = ref(false)
const userMenuOpen = ref(false)
const toolsMenuOpen = ref(false)
const toolsMenuRef = ref(null)
const unreadCount = ref(0)
const unreadPollInterval = ref(null)

// Computed from stores
const isLoggedIn = computed(() => userStore.isAuthenticated)
const authLoading = computed(() => userStore.isLoading)
const username = computed(() => userStore.username)
const userEmail = computed(() => userStore.email)
const userId = computed(() => userStore.userId)
const isAdmin = computed(() => userStore.isAdmin)

// Pro features (Phase 7/8/9) - all gated by subscription via capabilitiesStore
const isPro = computed(() => capabilitiesStore.isPro)

// Pro features: Observability visible for all Pro users
const showObservability = computed(() => capabilitiesStore.showObservability || isPro.value)
// Enterprise intranet deployment: Orchestrator / Queues / RPA suite.
// isEnterprise === (deploymentMode === 'enterprise_intranet'); mirrors the
// /enterprise route guard in router.js (enterpriseFeatureMap).
const isEnterprise = computed(() => capabilitiesStore.isEnterprise)
// Enterprise features: Audit Logs only for enterprise license
const showAuditLog = computed(() => capabilitiesStore.showAuditLog)
const showOrgSettings = computed(() => capabilitiesStore.showOrgSettings)
const showRbacSettings = computed(() => capabilitiesStore.showRbacSettings)
const showMarketplace = computed(() => capabilitiesStore.showMarketplace)
const showSubscriptions = computed(() => capabilitiesStore.showSubscriptions)

// Trial (cloud only — desktop returns null → false)
const isTrialActive = computed(() => capabilitiesStore.isTrialActive)
const trialDaysRemaining = computed(() => capabilitiesStore.trialDaysRemaining ?? 0)

// Product Switcher — Tauri uses IPC to switch WebView, web uses URL redirect
const cortexUrl = computed(() => {
  return import.meta.env.VITE_CORTEX_URL || 'https://cortex.flyto2.com'
})

async function switchToCortex() {
  userMenuOpen.value = false
  if (window.__TAURI_INTERNALS__) {
    // Desktop: pass the validated access token so Cortex WebView auto-signs
    // in. authAPI.getAccessToken() returns null for stale/expired tokens,
    // so Cortex won't be handed a token that will instantly 401 there.
    const authToken = authAPI.getAccessToken()
    window.__TAURI_INTERNALS__.invoke('switch_product', { target: 'cortex', authToken })
  } else {
    // Web: subdomain redirect
    window.location.href = cortexUrl.value
  }
}

// Methods
async function handleLogout() {
  await userStore.logout()
  mobileMenuOpen.value = false
  userMenuOpen.value = false
  unreadCount.value = 0
  stopUnreadPoll()
}

// Fetch unread message count
async function fetchUnreadCount() {
  if (!isLoggedIn.value) return
  try {
    const result = await get(ENDPOINTS.CHAT.CONVERSATIONS, {
      params: { page: 1, pageSize: 100 }
    })
    // Sum up unread counts from all conversations
    const conversations = result.items || []
    let total = 0
    for (const conv of conversations) {
      const counts = conv.unreadCounts || {}
      total += counts[userId.value] || 0
    }
    unreadCount.value = total
  } catch (err) {
    // Silent fail
  }
}

function startUnreadPoll() {
  stopUnreadPoll()
  fetchUnreadCount()
  // Poll for unread message count
  unreadPollInterval.value = setInterval(fetchUnreadCount, DEFAULTS.TIMING.POLL_UNREAD_MESSAGES)
}

function stopUnreadPoll() {
  if (unreadPollInterval.value) {
    clearInterval(unreadPollInterval.value)
    unreadPollInterval.value = null
  }
}

// Close dropdown when clicking outside
function handleClickOutside(event) {
  if (userMenuOpen.value && !event.target.closest('.relative')) {
    userMenuOpen.value = false
  }
  if (toolsMenuOpen.value && toolsMenuRef.value && !toolsMenuRef.value.contains(event.target)) {
    toolsMenuOpen.value = false
  }
}

// Watch route changes to close menus
watch(route, () => {
  userMenuOpen.value = false
  toolsMenuOpen.value = false
})

// Watch auth state changes for unread polling
watch(
  [isLoggedIn, authLoading],
  ([loggedIn, loading]) => {
    if (!loading && loggedIn) {
      startUnreadPoll()
      walletStore.fetchBalance()
    } else if (!loggedIn) {
      stopUnreadPoll()
      walletStore.reset()
    }
  },
  { immediate: true }
)

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  // Fetch wallet balance for navbar badge
  if (userStore.isAuthenticated) {
    walletStore.fetchBalance()
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  stopUnreadPoll()
})
</script>

<style scoped>
.nav-link {
  @apply flex items-center gap-2 px-3 py-2 text-gray-600 dark:text-gray-300 font-medium text-sm rounded-lg transition-all duration-200;
}

.nav-link:hover {
  @apply text-primary-600 dark:text-primary-400 bg-gray-50 dark:bg-gray-700;
}

.nav-link.router-link-active {
  @apply text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/30;
}

.mobile-nav-link {
  @apply flex items-center gap-3 px-4 py-3 text-gray-700 dark:text-gray-300 font-medium rounded-lg transition-all duration-200;
}

.mobile-nav-link:hover {
  @apply text-primary-600 dark:text-primary-400 bg-gray-50 dark:bg-gray-700;
}

.mobile-nav-link.router-link-active {
  @apply text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/30;
}

.menu-item {
  @apply flex items-center gap-3 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors;
}

.menu-item.router-link-active {
  @apply text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/30;
}

.dropdown-item {
  @apply flex items-center gap-2 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors w-full;
}

.dropdown-item.router-link-active {
  @apply text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-900/30;
}
</style>

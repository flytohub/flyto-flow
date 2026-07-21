<template>
  <section v-if="showSection" class="py-8 bg-gray-900/50">
    <div class="container px-4">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-bold text-white flex items-center gap-2">
          <Zap :size="20" class="text-primary-400" />
          {{ $t('usage.dashboard.title', 'Usage Overview') }}
        </h2>
        <router-link
          to="/subscription"
          class="text-xs text-primary-400 hover:text-primary-300 flex items-center gap-1"
        >
          {{ $t('usage.managePlan', 'Manage Plan') }}
          <ExternalLink :size="12" />
        </router-link>
      </div>

      <!-- ===== Pro Users: Points Usage + Chart ===== -->
      <template v-if="isPro">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- Current Usage Card -->
          <div class="bg-gray-800/50 border border-gray-700/50 rounded-2xl p-6 backdrop-blur-sm">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-8 h-8 rounded-lg bg-primary-500/20 flex items-center justify-center">
                <Gauge :size="16" class="text-primary-400" />
              </div>
              <span class="text-xs text-gray-500 uppercase tracking-wider">
                {{ $t('usage.dashboard.currentUsage', 'Current Usage') }}
              </span>
            </div>

            <!-- Points display -->
            <div class="mb-4">
              <div class="text-3xl font-bold text-white font-mono mb-1">
                {{ formattedUsage }}
                <span v-if="pointsLimit" class="text-lg text-gray-500">
                  / {{ formattedLimit }}
                </span>
              </div>
              <p class="text-xs text-gray-500">
                {{ $t('usage.points', 'points') }}
                <span v-if="billingPeriod.end">
                  · {{ $t('usage.dashboard.resetsOn', { date: formatDate(billingPeriod.end) }) }}
                </span>
              </p>
            </div>

            <!-- Progress bar -->
            <div class="mb-4">
              <div class="h-2 bg-gray-700 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :class="progressClass"
                  :style="{ width: `${usagePercentage || 0}%` }"
                />
              </div>
            </div>

            <!-- Status -->
            <div class="flex items-center gap-2">
              <div
                class="w-2 h-2 rounded-full"
                :class="statusDotClass"
              />
              <span class="text-sm" :class="statusTextClass">
                {{ statusText }}
              </span>
            </div>
          </div>

          <!-- Usage Chart -->
          <div class="lg:col-span-2 bg-gray-800/50 border border-gray-700/50 rounded-2xl backdrop-blur-sm overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-700/50 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-400">
                {{ $t('usage.dashboard.usageHistory', 'Usage History') }}
              </h3>
              <div class="flex items-center gap-2">
                <button
                  v-for="type in chartTypes"
                  :key="type.value"
                  class="px-2 py-1 text-xs rounded transition-colors"
                  :class="selectedChartType === type.value
                    ? 'bg-primary-500/20 text-primary-400'
                    : 'text-gray-500 hover:text-gray-400'"
                  @click="selectedChartType = type.value"
                >
                  {{ type.label }}
                </button>
              </div>
            </div>

            <div class="p-6">
              <UsageChart
                :chart-data="usageHistory"
                :type="selectedChartType"
                :height="180"
                :is-loading="historyLoading"
                :show-limit="pointsLimit"
              />
            </div>
          </div>
        </div>

        <!-- Top Modules -->
        <div v-if="topModules.length > 0" class="mt-6">
          <h3 class="text-sm font-medium text-gray-400 mb-3">
            {{ $t('usage.dashboard.topModules', 'Top Modules This Period') }}
          </h3>
          <div class="flex flex-wrap gap-2">
            <div
              v-for="module in topModules"
              :key="module.moduleId"
              class="flex items-center gap-2 px-3 py-1.5 bg-gray-800/50 border border-gray-700/50 rounded-lg"
            >
              <div
                class="w-2 h-2 rounded-full"
                :style="{ backgroundColor: getModuleColor(module.moduleId) }"
              />
              <span class="text-sm text-gray-300">{{ module.moduleId }}</span>
              <span class="text-xs text-gray-500">{{ formatCompactNumber(module.totalPoints) }}</span>
            </div>
          </div>
        </div>
      </template>

      <!-- ===== Feature Quota Cards (all users) ===== -->
      <template v-if="quotaEntries.length > 0">
        <p v-if="!isPro" class="text-sm text-gray-500 mb-4 mt-6">
          {{ $t('usage.quota.subtitle', 'Your free plan usage this period') }}
        </p>
        <h3 v-else class="text-sm font-medium text-gray-400 mb-4 mt-6">
          {{ $t('usage.quota.title', 'Feature Quotas') }}
        </h3>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="q in quotaEntries"
            :key="q.id"
            class="bg-gray-800/50 border rounded-xl p-4 backdrop-blur-sm"
            :class="q.enabled ? 'border-gray-700/50' : 'border-gray-700/30 opacity-60'"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="text-sm font-medium text-gray-200">{{ q.label }}</span>
              <span
                class="text-xs px-1.5 py-0.5 rounded"
                :class="quotaBadgeClass(q)"
              >
                {{ quotaBadgeText(q) }}
              </span>
            </div>

            <!-- Progress bar (only for enabled features with numeric limits) -->
            <div v-if="q.enabled && !q.unlimited && q.limit > 0" class="mb-2">
              <div class="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :class="quotaBarClass(q)"
                  :style="{ width: `${Math.min(100, q.pct)}%` }"
                />
              </div>
            </div>

            <div class="flex items-center justify-between">
              <span v-if="!q.enabled" class="text-xs text-gray-600">
                {{ $t('usage.quota.disabled', 'Pro only') }}
              </span>
              <span v-else-if="q.unlimited" class="text-xs text-gray-500">
                {{ $t('usage.quota.unlimited', 'Unlimited') }}
              </span>
              <span v-else class="text-xs text-gray-500">
                {{ q.current }} / {{ q.limit }} {{ unitLabel(q.unit) }}
              </span>
              <span v-if="q.enabled && !q.unlimited && q.remaining <= 0" class="text-xs text-red-400">
                {{ $t('usage.quota.exhausted', 'Exhausted') }}
              </span>
            </div>
          </div>
        </div>

        <!-- Upgrade CTA (Free only) -->
        <div v-if="!isPro" class="mt-4 text-center">
          <router-link
            to="/subscription"
            class="inline-flex items-center gap-1.5 text-sm text-primary-400 hover:text-primary-300 transition-colors"
          >
            <Zap :size="14" />
            {{ $t('usage.quota.upgrade', 'Upgrade for unlimited access') }}
          </router-link>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useI18n } from 'vue-i18n'
import { Zap, Gauge, ExternalLink } from 'lucide-vue-next'
import { formatCompactNumber } from '@/utils/format'
import UsageChart from '@/components/common/UsageChart.vue'
import { useCapabilitiesStore } from '@/stores/capabilitiesStore'
import { useUsageStore } from '@/stores/usageStore'
import { useUserStore } from '@/stores/userStore'

const { t } = useI18n()
const capabilitiesStore = useCapabilitiesStore()
const usageStore = useUsageStore()
const userStore = useUserStore()

const selectedChartType = ref('bar')
const historyLoading = ref(false)

const chartTypes = [
  { value: 'bar', label: 'Bar' },
  { value: 'line', label: 'Line' },
]

const isPro = computed(() => capabilitiesStore.isPro)

// Show for all authenticated users (Pro: points, Free: quotas)
const showSection = computed(() => userStore.isAuthenticated)

const {
  formattedUsage,
  formattedLimit,
  pointsLimit,
  usagePercentage,
  isNearLimit,
  isOverLimit,
  billingPeriod,
  topModules,
  usageHistory,
  featureQuotas,
} = storeToRefs(usageStore)

// ===== Feature name mapping (reuse admin i18n keys) =====
const FEATURE_LABELS = {
  'execution.debug': 'admin.planLimits.featureDebug',
  'execution.replay': 'admin.planLimits.featureReplay',
  'execution.rerun': 'admin.planLimits.featureRerun',
  'core.execution_record_full': 'admin.planLimits.featureFullRecord',
  'local.metrics': 'admin.planLimits.featureMetrics',
  'local.tracing': 'admin.planLimits.featureTracing',
  'local.alerts': 'admin.planLimits.featureAlerts',
  'local.versioning': 'admin.planLimits.featureVersioning',
  'local.version_rollback': 'admin.planLimits.featureRollback',
  'local.audit': 'admin.planLimits.featureAudit',
  'pro.modules.stealth': 'admin.planLimits.featureStealth',
  'pro.modules.captcha': 'admin.planLimits.featureCaptcha',
  'pro.modules.parallel': 'admin.planLimits.featureParallel',
  'pro.modules.document': 'admin.planLimits.featureDocument',
  'pro.modules.vision': 'admin.planLimits.featureVision',
}

// ===== Free user quota entries =====
const quotaEntries = computed(() => {
  const quotas = featureQuotas.value
  if (!quotas || typeof quotas !== 'object') return []

  return Object.entries(quotas).map(([id, q]) => {
    const current = q.current ?? 0
    const limit = q.limit ?? null
    const remaining = q.remaining ?? null
    const enabled = q.enabled ?? false
    const unit = q.unit ?? 'count_per_month'
    const unlimited = q.unlimited ?? (limit === null)
    const pct = q.pct ?? 0

    const i18nKey = FEATURE_LABELS[id]
    const label = i18nKey ? t(i18nKey, id.split('.').pop()) : id

    return { id, label, enabled, current, limit, remaining, pct, unlimited, unit }
  })
})

// Quota badge styling
function quotaBadgeClass(q) {
  if (!q.enabled) return 'bg-gray-700/50 text-gray-500'
  if (q.unlimited) return 'bg-primary-500/20 text-primary-400'
  if (q.remaining <= 0) return 'bg-red-500/20 text-red-400'
  if (q.pct >= 80) return 'bg-amber-500/20 text-amber-400'
  return 'bg-emerald-500/20 text-emerald-400'
}

function unitLabel(unit) {
  const labels = {
    count_per_month: t('usage.unit.countPerMonth'),
    count_total: t('usage.unit.countTotal'),
    days: t('usage.unit.days'),
  }
  return labels[unit] || ''
}

function quotaBadgeText(q) {
  if (!q.enabled) return t('usage.quota.disabled')
  if (q.unlimited) return t('usage.quota.unlimited')
  if (q.remaining <= 0) return t('usage.quota.exhausted')
  const unit = unitLabel(q.unit)
  return `${q.remaining} ${unit}`
}

function quotaBarClass(q) {
  if (q.remaining <= 0) return 'bg-red-500'
  if (q.pct >= 80) return 'bg-amber-500'
  return 'bg-primary-500'
}

// ===== Pro user computed =====
const progressClass = computed(() => {
  if (isOverLimit.value) return 'bg-red-500'
  if (isNearLimit.value) return 'bg-amber-500'
  return 'bg-primary-500'
})

const statusDotClass = computed(() => {
  if (isOverLimit.value) return 'bg-red-400'
  if (isNearLimit.value) return 'bg-amber-400'
  return 'bg-emerald-400'
})

const statusTextClass = computed(() => {
  if (isOverLimit.value) return 'text-red-400'
  if (isNearLimit.value) return 'text-amber-400'
  return 'text-gray-400'
})

const statusText = computed(() => {
  if (isOverLimit.value) return t('usage.status.limitReached', 'Limit reached')
  if (isNearLimit.value) return t('usage.status.nearLimit', 'Near limit')
  if (pointsLimit.value === null) return t('usage.status.unlimited', 'Unlimited')
  return t('usage.status.normal', 'Normal')
})


function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}


function getModuleColor(moduleId) {
  let hash = 0
  for (let i = 0; i < moduleId.length; i++) {
    hash = moduleId.charCodeAt(i) + ((hash << 5) - hash)
  }
  const colors = [
    '#6366f1', '#8b5cf6', '#ec4899', '#f59e0b',
    '#10b981', '#3b82f6', '#ef4444', '#06b6d4',
  ]
  return colors[Math.abs(hash) % colors.length]
}

// ===== Data loading =====
async function loadUsageData() {
  if (!userStore.isAuthenticated) return

  // All users load feature quotas
  await usageStore.fetchFeatureQuotas()

  if (isPro.value) {
    await usageStore.fetchCurrentUsage()
    historyLoading.value = true
    try {
      await usageStore.fetchHistory({ period: 'month', limit: 6 })
    } finally {
      historyLoading.value = false
    }
  }
}

onMounted(() => {
  if (userStore.isAuthenticated) {
    loadUsageData()
  }
})

watch(
  () => userStore.isAuthenticated,
  (isAuth) => {
    if (isAuth) {
      loadUsageData()
    }
  }
)
</script>

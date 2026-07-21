<template>
  <section id="recent-activity" class="py-6 bg-gray-50 dark:bg-gray-900">
    <div class="container px-4">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Activity :size="20" class="text-blue-500" />
          {{ $t('dashboardPage.recentActivity.title') }}
        </h2>
        <button
          @click="$emit('refresh')"
          class="p-2 text-gray-400 hover:(text-gray-600 bg-gray-100) dark:hover:(text-gray-300 bg-gray-700) rounded-lg transition-colors"
          :disabled="loading"
        >
          <RefreshCw :size="18" :class="{ 'animate-spin': loading }" />
        </button>
      </div>

      <!-- Activity List Skeleton -->
      <div v-if="loading" class="space-y-3">
        <div
          v-for="i in 3"
          :key="i"
          class="bg-white border border-gray-200 rounded-xl p-4 dark:(bg-gray-800 border-gray-700)"
        >
          <div class="flex items-center gap-4">
            <div class="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700 animate-pulse flex-shrink-0"></div>
            <div class="flex-1 space-y-2">
              <div class="flex items-center gap-2">
                <div class="h-5 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                <div class="h-5 w-16 bg-gray-200 dark:bg-gray-700 rounded-full animate-pulse"></div>
              </div>
              <div class="h-3 w-48 bg-gray-100 dark:bg-gray-700 rounded animate-pulse"></div>
            </div>
            <div class="h-8 w-20 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse flex-shrink-0"></div>
          </div>
        </div>
      </div>

      <!-- Activity List -->
      <div v-else-if="activities.length > 0" class="space-y-3">
        <div
          v-for="activity in activities"
          :key="activity.id"
          class="bg-white border border-gray-200 rounded-xl p-4 hover:shadow-md transition-shadow dark:(bg-gray-800 border-gray-700)"
        >
          <div class="flex items-center gap-4">
            <!-- Icon -->
            <div
              class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
              :class="activity.type === 'sale' ? 'bg-emerald-100 text-emerald-600 dark:(bg-emerald-900/30 text-emerald-400)' : getStatusIconClass(activity.status)"
            >
              <component :is="activity.type === 'sale' ? DollarSign : getStatusIcon(activity.status)" :size="20" />
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <h3 class="font-semibold text-gray-900 dark:text-white truncate">{{ activity.templateName }}</h3>
                <span
                  class="px-2 py-0.5 text-xs font-medium rounded-full"
                  :class="activity.type === 'sale' ? 'bg-emerald-100 text-emerald-700 dark:(bg-emerald-900/30 text-emerald-400)' : getStatusBadgeClass(activity.status)"
                >
                  {{ activity.type === 'sale' ? $t('dashboardPage.recentActivity.sale') : getStatusLabel(activity.status) }}
                </span>
              </div>
              <div class="flex items-center gap-3 mt-1 text-xs text-gray-500 dark:text-gray-400">
                <template v-if="activity.type === 'execution'">
                  <span>{{ formatRelativeTime(activity.startedAt) }}</span>
                  <span v-if="activity.executionTime">
                    {{ $t('dashboardPage.recentActivity.duration', { time: activity.executionTime.toFixed(1) }) }}
                  </span>
                </template>
                <template v-else>
                  <span>{{ $t('dashboardPage.recentActivity.soldTo', { buyer: activity.buyerEmail }) }}</span>
                  <span class="text-emerald-600 dark:text-emerald-400 font-medium">
                    +{{ formatCurrency(activity.amount || 0) }}
                  </span>
                  <span>{{ formatRelativeTime(activity.purchasedAt) }}</span>
                </template>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex items-center gap-2 flex-shrink-0">
              <template v-if="activity.type === 'execution'">
                <button
                  v-if="activity.status === 'success'"
                  @click="$emit('view-result', activity)"
                  class="px-3 py-1.5 bg-gray-100 text-gray-700 text-xs font-medium rounded-lg transition-colors hover:bg-gray-200 dark:(bg-gray-700 text-gray-300 hover:bg-gray-600)"
                >
                  {{ $t('dashboardPage.recentActivity.viewResult') }}
                </button>
                <button
                  v-else-if="activity.status === 'failed'"
                  @click="$emit('retry', activity)"
                  class="px-3 py-1.5 bg-red-100 text-red-700 text-xs font-medium rounded-lg transition-colors hover:bg-red-200 dark:(bg-red-900/30 text-red-400 hover:bg-red-900/50)"
                >
                  {{ $t('dashboardPage.recentActivity.retry') }}
                </button>
                <button
                  v-else-if="activity.status === 'running'"
                  class="px-3 py-1.5 bg-blue-100 text-blue-700 text-xs font-medium rounded-lg flex items-center gap-1 dark:(bg-blue-900/30 text-blue-400)"
                  disabled
                >
                  <Loader2 :size="12" class="animate-spin" />
                  {{ $t('dashboardPage.recentActivity.running') }}
                </button>
              </template>
            </div>
          </div>

          <!-- Error Message -->
          <div
            v-if="activity.type === 'execution' && activity.status === 'failed' && activity.errorMessage"
            class="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg dark:(bg-red-900/20 border-red-800)"
          >
            <p class="text-xs text-red-600 dark:text-red-400 font-mono truncate">{{ activity.errorMessage }}</p>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="!loading" class="text-center py-12">
        <div class="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
          <Activity :size="32" class="text-gray-400" />
        </div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          {{ $t('dashboardPage.recentActivity.noActivity') }}
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          {{ $t('dashboardPage.recentActivity.runTemplateFirst') }}
        </p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { Activity, RefreshCw, Loader2, CheckCircle, XCircle, Clock, DollarSign } from 'lucide-vue-next'
import { useRelativeTime } from '@/composables/useRelativeTime'
import { formatCurrency } from '@/utils/format'

const { t } = useI18n()
const { formatRelativeTime } = useRelativeTime()

defineProps({
  activities: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

defineEmits(['refresh', 'view-result', 'retry'])

function getStatusIcon(status) {
  switch (status) {
    case 'success': return CheckCircle
    case 'failed': return XCircle
    case 'running': return Loader2
    default: return Clock
  }
}

function getStatusIconClass(status) {
  switch (status) {
    case 'success': return 'bg-emerald-100 text-emerald-600 dark:(bg-emerald-900/30 text-emerald-400)'
    case 'failed': return 'bg-red-100 text-red-600 dark:(bg-red-900/30 text-red-400)'
    case 'running': return 'bg-blue-100 text-blue-600 dark:(bg-blue-900/30 text-blue-400)'
    default: return 'bg-gray-100 text-gray-600 dark:(bg-gray-700 text-gray-400)'
  }
}

function getStatusBadgeClass(status) {
  switch (status) {
    case 'success': return 'bg-emerald-100 text-emerald-700 dark:(bg-emerald-900/30 text-emerald-400)'
    case 'failed': return 'bg-red-100 text-red-700 dark:(bg-red-900/30 text-red-400)'
    case 'running': return 'bg-blue-100 text-blue-700 dark:(bg-blue-900/30 text-blue-400)'
    default: return 'bg-gray-100 text-gray-700 dark:(bg-gray-700 text-gray-400)'
  }
}

function getStatusLabel(status) {
  switch (status) {
    case 'success': return t('dashboardPage.recentActivity.success')
    case 'failed': return t('dashboardPage.recentActivity.failed')
    case 'running': return t('dashboardPage.recentActivity.running')
    default: return status
  }
}

</script>

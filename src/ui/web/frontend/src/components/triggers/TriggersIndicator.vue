<template>
  <div class="triggers-indicator" ref="containerRef">
    <!-- Trigger Button -->
    <button
      @click="toggleDropdown"
      class="trigger-btn"
      :class="{ 'has-active': activeCount > 0 }"
    >
      <Clock :size="20" />
      <span v-if="activeCount > 0" class="active-badge">
        {{ activeCount > 99 ? '99+' : activeCount }}
      </span>
    </button>

    <!-- Dropdown -->
    <Transition name="dropdown">
      <div v-if="isOpen" class="triggers-dropdown">
        <!-- Header -->
        <div class="dropdown-header">
          <h3 class="dropdown-title">{{ $t('triggers.indicator.title') }}</h3>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="loading-state">
          <Loader2 class="spinner" :size="24" />
        </div>

        <!-- Empty State -->
        <div v-else-if="items.length === 0" class="empty-state">
          <CalendarOff :size="40" class="empty-icon" />
          <p class="empty-text">{{ $t('triggers.indicator.empty') }}</p>
        </div>

        <!-- Trigger List -->
        <div v-else class="trigger-list">
          <div
            v-for="item in items"
            :key="item.id"
            class="trigger-item"
          >
            <!-- Icon -->
            <div class="trigger-icon" :class="item.type === 'schedule' ? 'icon-schedule' : 'icon-webhook'">
              <Clock v-if="item.type === 'schedule'" :size="16" />
              <Webhook v-else :size="16" />
            </div>

            <!-- Content -->
            <div class="trigger-content">
              <p class="trigger-name">{{ item.name }}</p>
              <p class="trigger-desc">
                <template v-if="item.type === 'schedule'">
                  {{ item.workflowName }} · {{ $t('triggers.nextRun') }}: {{ item.nextRun }}
                </template>
                <template v-else>
                  {{ item.workflowName }} · {{ $t('triggers.indicator.triggeredCount', { count: item.triggerCount }) }}
                </template>
              </p>
            </div>

            <button @click.stop="openDetail(item)" class="trigger-info-btn" :title="$t('common.details', 'Details')">
              <Info :size="18" />
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Detail Modal -->
    <BaseModal :show="showDetail" @close="showDetail = false" size="lg" :title="detailData?.name || ''">
      <div v-if="detailData" class="space-y-4">
        <!-- Schedule Detail -->
        <template v-if="selectedItem?.type === 'schedule'">
          <!-- 基本資訊 -->
          <div class="p-4 bg-gray-700/30 rounded-lg">
            <p class="text-xs text-gray-500 mb-3">{{ $t('scheduler.detail.basicInfo', 'Basic Info') }}</p>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.name', 'Name') }}</p>
                <p class="text-white">{{ detailData.name }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.status', 'Status') }}</p>
                <span
                  class="px-2 py-0.5 text-xs rounded-full"
                  :class="{
                    'bg-green-500/20 text-green-400': detailData.status === 'active',
                    'bg-yellow-500/20 text-yellow-400': detailData.status === 'paused',
                    'bg-gray-500/20 text-gray-400': detailData.status === 'disabled'
                  }"
                >
                  {{ detailData.status }}
                </span>
              </div>
              <div v-if="detailData.description" class="col-span-2">
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.description', 'Description') }}</p>
                <p class="text-gray-300">{{ detailData.description }}</p>
              </div>
            </div>
          </div>

          <!-- 排程設定 -->
          <div class="p-4 bg-gray-700/30 rounded-lg">
            <p class="text-xs text-gray-500 mb-3">{{ $t('scheduler.detail.scheduleConfig', 'Schedule Config') }}</p>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-xs text-gray-500">{{ detailData.cronExpression ? 'Cron' : 'Interval' }}</p>
                <p class="text-white font-mono">{{ detailData.cronExpression || `${detailData.intervalSeconds}s` }}</p>
              </div>
              <div v-if="detailData.timezone">
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.timezone', 'Timezone') }}</p>
                <p class="text-white">{{ detailData.timezone }}</p>
              </div>
              <div v-if="detailData.nextRunAt" class="col-span-2">
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.nextRun', 'Next Run') }}</p>
                <p class="text-white">
                  {{ formatRelativeTime(detailData.nextRunAt) }}
                  <span class="text-gray-400 text-sm ml-1">({{ formatDateTime(detailData.nextRunAt) }})</span>
                </p>
              </div>
            </div>
          </div>

          <!-- 執行統計 -->
          <div class="p-4 bg-gray-700/30 rounded-lg">
            <p class="text-xs text-gray-500 mb-3">{{ $t('scheduler.detail.executionStats', 'Execution Stats') }}</p>
            <div class="grid grid-cols-3 gap-4">
              <div>
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.runCount', 'Run Count') }}</p>
                <p class="text-white">{{ detailData.runCount }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.failureCount', 'Failure Count') }}</p>
                <p :class="detailData.failureCount > 0 ? 'text-red-400' : 'text-white'">{{ detailData.failureCount }}</p>
              </div>
              <div v-if="detailData.lastRunAt">
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.lastRun', 'Last Run') }}</p>
                <p class="text-white">{{ formatDateTime(detailData.lastRunAt) }}</p>
              </div>
            </div>
          </div>

          <!-- 關聯 -->
          <div class="p-4 bg-gray-700/30 rounded-lg">
            <p class="text-xs text-gray-500 mb-3">{{ $t('scheduler.detail.association', 'Association') }}</p>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.workflow', 'Workflow') }}</p>
                <p class="text-white">{{ detailData.workflowName }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">ID</p>
                <p class="text-gray-400 font-mono text-sm">{{ detailData.workflowId }}</p>
              </div>
            </div>
          </div>

          <!-- 時間戳 -->
          <div class="p-4 bg-gray-700/30 rounded-lg">
            <p class="text-xs text-gray-500 mb-3">{{ $t('scheduler.detail.timestamps', 'Timestamps') }}</p>
            <div class="grid grid-cols-2 gap-4">
              <div v-if="detailData.createdAt">
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.createdAt', 'Created At') }}</p>
                <p class="text-white">{{ formatDateTime(detailData.createdAt) }}</p>
              </div>
              <div v-if="detailData.updatedAt">
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.updatedAt', 'Updated At') }}</p>
                <p class="text-white">{{ formatDateTime(detailData.updatedAt) }}</p>
              </div>
            </div>
          </div>
        </template>

        <!-- Webhook Detail -->
        <template v-else>
          <!-- 基本資訊 -->
          <div class="p-4 bg-gray-700/30 rounded-lg">
            <p class="text-xs text-gray-500 mb-3">{{ $t('scheduler.detail.basicInfo', 'Basic Info') }}</p>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.name', 'Name') }}</p>
                <p class="text-white">{{ detailData.name }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.status', 'Status') }}</p>
                <span
                  class="px-2 py-0.5 text-xs rounded-full"
                  :class="detailData.status === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'"
                >
                  {{ detailData.status }}
                </span>
              </div>
              <div v-if="detailData.provider">
                <p class="text-xs text-gray-500">Provider</p>
                <span class="px-2 py-0.5 text-xs rounded-full bg-cyan-500/20 text-cyan-400">{{ detailData.provider }}</span>
              </div>
              <div v-if="detailData.description" class="col-span-2">
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.description', 'Description') }}</p>
                <p class="text-gray-300">{{ detailData.description }}</p>
              </div>
            </div>
          </div>

          <!-- 觸發 URL -->
          <div v-if="detailData.triggerUrl" class="p-4 bg-gray-700/30 rounded-lg">
            <p class="text-xs text-gray-500 mb-3">{{ $t('scheduler.detail.triggerUrl', 'Trigger URL') }}</p>
            <div class="flex items-center gap-2">
              <code class="flex-1 px-3 py-2 bg-gray-800 rounded-lg text-cyan-400 text-sm font-mono truncate">{{ detailData.triggerUrl }}</code>
              <button
                @click="copyToClipboard(detailData.triggerUrl)"
                class="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors shrink-0"
                :title="$t('common.copy', 'Copy')"
              >
                <component :is="copiedUrl ? Check : Copy" :size="16" :class="copiedUrl ? 'text-green-400' : ''" />
              </button>
            </div>
          </div>

          <!-- 安全 -->
          <div class="p-4 bg-gray-700/30 rounded-lg">
            <p class="text-xs text-gray-500 mb-3">{{ $t('scheduler.detail.security', 'Security') }}</p>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.signatureVerification', 'Signature Verification') }}</p>
                <p class="text-white">{{ detailData.requireSignature ? $t('common.yes', 'Yes') : $t('common.no', 'No') }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.ipWhitelist', 'IP Whitelist') }}</p>
                <p class="text-white">{{ detailData.allowedIps?.length ? detailData.allowedIps.join(', ') : $t('common.none', 'None') }}</p>
              </div>
            </div>
          </div>

          <!-- 統計 -->
          <div class="p-4 bg-gray-700/30 rounded-lg">
            <p class="text-xs text-gray-500 mb-3">{{ $t('scheduler.detail.stats', 'Stats') }}</p>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.triggerCount', 'Trigger Count') }}</p>
                <p class="text-white">{{ detailData.triggerCount }}</p>
              </div>
              <div v-if="detailData.lastTriggeredAt">
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.lastTriggered', 'Last Triggered') }}</p>
                <p class="text-white">{{ formatDateTime(detailData.lastTriggeredAt) }}</p>
              </div>
            </div>
          </div>

          <!-- 關聯 -->
          <div class="p-4 bg-gray-700/30 rounded-lg">
            <p class="text-xs text-gray-500 mb-3">{{ $t('scheduler.detail.association', 'Association') }}</p>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.workflow', 'Workflow') }}</p>
                <p class="text-white">{{ detailData.workflowName }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">ID</p>
                <p class="text-gray-400 font-mono text-sm">{{ detailData.workflowId }}</p>
              </div>
            </div>
          </div>

          <!-- 時間戳 -->
          <div class="p-4 bg-gray-700/30 rounded-lg">
            <p class="text-xs text-gray-500 mb-3">{{ $t('scheduler.detail.timestamps', 'Timestamps') }}</p>
            <div class="grid grid-cols-2 gap-4">
              <div v-if="detailData.createdAt">
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.createdAt', 'Created At') }}</p>
                <p class="text-white">{{ formatDateTime(detailData.createdAt) }}</p>
              </div>
              <div v-if="detailData.updatedAt">
                <p class="text-xs text-gray-500">{{ $t('scheduler.detail.updatedAt', 'Updated At') }}</p>
                <p class="text-white">{{ formatDateTime(detailData.updatedAt) }}</p>
              </div>
            </div>
          </div>
        </template>
      </div>
    </BaseModal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Clock, Webhook, CalendarOff, Loader2, Info, Copy, Check } from 'lucide-vue-next'
import { listSchedules, listWebhooks } from '@/api/triggers'
import BaseModal from '@/components/common/BaseModal.vue'
import { useRelativeTime } from '@/composables/useRelativeTime'
import { DEFAULTS } from '@/config/defaults'

const { t } = useI18n()
const { formatRelativeTime } = useRelativeTime()
const containerRef = ref(null)
const isOpen = ref(false)
const loading = ref(false)
const schedules = ref([])
const webhooks = ref([])
const selectedItem = ref(null)
const showDetail = ref(false)
const copiedUrl = ref(false)

const items = computed(() => {
  const result = []

  for (const s of schedules.value) {
    if (s.status !== 'active') continue
    result.push({
      id: `schedule-${s.id}`,
      type: 'schedule',
      name: s.name,
      workflowName: s.workflowName || s.templateName || s.workflowId || '-',
      nextRun: s.nextRunAt ? formatNextRun(s.nextRunAt) : '-',
      raw: s
    })
  }

  for (const w of webhooks.value) {
    if (w.status !== 'active') continue
    result.push({
      id: `webhook-${w.id}`,
      type: 'webhook',
      name: w.name,
      workflowName: w.workflowName || w.templateName || w.workflowId || '-',
      triggerCount: w.triggerCount ?? 0,
      raw: w
    })
  }

  return result
})

const activeCount = computed(() => items.value.length)

const detailData = computed(() => {
  if (!selectedItem.value) return null
  const r = selectedItem.value.raw
  if (!r) return null

  // Helper: try snake_case then camelCase
  const f = (snake) => {
    const camel = snake.replace(/_([a-z])/g, (_, c) => c.toUpperCase())
    return r[snake] ?? r[camel]
  }

  if (selectedItem.value.type === 'schedule') {
    return {
      name: r.name,
      status: r.status,
      description: f('description') || '',
      cronExpression: f('cron_expression') || '',
      intervalSeconds: f('interval_seconds') || 0,
      timezone: f('timezone') || '',
      nextRunAt: f('next_run_at') || '',
      lastRunAt: f('last_run_at') || '',
      runCount: f('run_count') ?? 0,
      failureCount: f('failure_count') ?? 0,
      workflowId: f('workflow_id') || '',
      workflowName: selectedItem.value.workflowName,
      createdAt: f('created_at') || '',
      updatedAt: f('updated_at') || '',
    }
  } else {
    return {
      name: r.name,
      status: r.status,
      provider: r.provider || '',
      description: f('description') || '',
      triggerUrl: f('trigger_url') || '',
      requireSignature: f('require_signature') ?? false,
      allowedIps: f('allowed_ips') || [],
      triggerCount: f('trigger_count') ?? 0,
      lastTriggeredAt: f('last_triggered_at') || '',
      workflowId: f('workflow_id') || '',
      workflowName: selectedItem.value.workflowName,
      createdAt: f('created_at') || '',
      updatedAt: f('updated_at') || '',
    }
  }
})

function openDetail(item) {
  selectedItem.value = item
  showDetail.value = true
}

function formatDateTime(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function copyToClipboard(text) {
  await navigator.clipboard.writeText(text)
  copiedUrl.value = true
  setTimeout(() => { copiedUrl.value = false }, 2000)
}

function formatNextRun(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()

  const time = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  if (isToday) return time
  return `${date.toLocaleDateString([], { month: 'short', day: 'numeric' })} ${time}`
}

function toggleDropdown() {
  isOpen.value = !isOpen.value
  if (isOpen.value && schedules.value.length === 0 && webhooks.value.length === 0) {
    fetchAll()
  }
}

async function fetchAll() {
  loading.value = true
  try {
    const [sRes, wRes] = await Promise.all([
      listSchedules().catch(() => ({})),
      listWebhooks().catch(() => ({}))
    ])
    schedules.value = sRes.schedules || []
    webhooks.value = wRes.webhooks || []
  } catch {
    // silent
  } finally {
    loading.value = false
  }
}

async function fetchCounts() {
  try {
    const [sRes, wRes] = await Promise.all([
      listSchedules().catch(() => ({})),
      listWebhooks().catch(() => ({}))
    ])
    schedules.value = sRes.schedules || []
    webhooks.value = wRes.webhooks || []
  } catch {
    // silent
  }
}

function handleClickOutside(event) {
  if (containerRef.value && !containerRef.value.contains(event.target)) {
    isOpen.value = false
  }
}

let pollInterval = null

onMounted(() => {
  fetchCounts()
  document.addEventListener('click', handleClickOutside)

  if (pollInterval) {
    clearInterval(pollInterval)
  }
  pollInterval = setInterval(fetchCounts, DEFAULTS.TIMING.POLL_TRIGGERS)
})

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.triggers-indicator {
  position: relative;
}

.trigger-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 0.2s;
}

.trigger-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.trigger-btn.has-active {
  color: #f97316;
}

.active-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: linear-gradient(135deg, #f97316, #ea580c);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.triggers-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 380px;
  max-height: 480px;
  background: rgba(30, 30, 40, 0.98);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  z-index: 1000;
}

.dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.dropdown-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: rgba(255, 255, 255, 0.4);
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  margin-bottom: 12px;
  opacity: 0.3;
}

.empty-text {
  margin: 0;
  font-size: 14px;
}

.trigger-list {
  flex: 1;
  overflow-y: auto;
  max-height: 400px;
}

.trigger-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 20px;
  transition: background 0.2s;
}

.trigger-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.trigger-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.trigger-icon.icon-schedule {
  background: rgba(249, 115, 22, 0.2);
  color: #fb923c;
}

.trigger-icon.icon-webhook {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.trigger-content {
  flex: 1;
  min-width: 0;
}

.trigger-name {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.trigger-desc {
  margin: 0;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Dropdown Animation */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.trigger-info-btn {
  flex-shrink: 0;
  align-self: center;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.3);
  cursor: pointer;
  transition: all 0.2s;
  opacity: 0;
}

.trigger-item:hover .trigger-info-btn {
  opacity: 1;
}

.trigger-info-btn:hover {
  background: rgba(6, 182, 212, 0.15);
  color: #22d3ee;
}

@media (max-width: 480px) {
  .triggers-dropdown {
    position: fixed;
    top: 60px;
    left: 10px;
    right: 10px;
    width: auto;
  }
}
</style>

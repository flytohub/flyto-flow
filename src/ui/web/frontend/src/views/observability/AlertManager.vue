<template>
  <div class="container mx-auto px-4 py-6">
    <!-- Active Alerts Section -->
    <div class="bg-gray-800 rounded-xl border border-gray-700 mb-6">
      <div class="p-4 border-b border-gray-700 flex items-center justify-between">
        <h3 class="text-lg font-semibold text-white flex items-center gap-2">
          <AlertTriangle :size="20" class="text-red-400" />
          {{ $t('alerts.active.title', 'Active Alerts') }}
          <span v-if="alertStore.activeCount > 0" class="ml-2 px-2 py-0.5 bg-red-500/20 text-red-400 text-sm rounded-full">
            {{ alertStore.activeCount }}
          </span>
        </h3>
        <button
          @click="refreshAlerts"
          :disabled="alertStore.isLoading"
          class="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
        >
          <RefreshCw :size="18" :class="{ 'animate-spin': alertStore.isLoading }" />
        </button>
      </div>

      <div class="p-4">
        <!-- Loading -->
        <div v-if="alertStore.isLoading && !alertStore.hasActiveAlerts" class="space-y-3">
          <div v-for="i in 3" :key="i" class="h-20 bg-gray-700/50 rounded-lg animate-pulse"></div>
        </div>

        <!-- Empty State -->
        <div v-else-if="!alertStore.hasActiveAlerts" class="py-8 text-center text-gray-400">
          <CheckCircle :size="48" class="mx-auto mb-3 text-green-400 opacity-50" />
          <p>{{ $t('alerts.active.empty', 'No active alerts') }}</p>
        </div>

        <!-- Alert Cards -->
        <div v-else class="space-y-3">
          <ActiveAlertCard
            v-for="alert in alertStore.activeAlerts"
            :key="alert.id"
            :alert="alert"
            :loading="alertStore.isLoading"
            @acknowledge="handleAcknowledge"
            @mute="handleMute"
          />
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="mb-6 border-b border-gray-700">
      <div class="flex gap-1">
        <button
          @click="activeTab = 'rules'"
          class="px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px"
          :class="activeTab === 'rules' ? 'text-purple-400 border-purple-400' : 'text-gray-400 border-transparent hover:text-white'"
        >
          <Settings :size="16" class="inline-block mr-2" />
          {{ $t('alerts.tabs.rules', 'Alert Rules') }}
        </button>
        <button
          @click="activeTab = 'history'"
          class="px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px"
          :class="activeTab === 'history' ? 'text-purple-400 border-purple-400' : 'text-gray-400 border-transparent hover:text-white'"
        >
          <History :size="16" class="inline-block mr-2" />
          {{ $t('alerts.tabs.history', 'Alert History') }}
        </button>
      </div>
    </div>

    <!-- Rules Tab -->
    <div v-show="activeTab === 'rules'" class="bg-gray-800 rounded-xl border border-gray-700">
      <div class="p-4 border-b border-gray-700 flex items-center justify-between">
        <h3 class="text-lg font-semibold text-white flex items-center gap-2">
          <Bell :size="20" class="text-purple-400" />
          {{ $t('alerts.rules.title', 'Alert Rules') }}
        </h3>
        <button
          @click="openCreateModal"
          class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg transition-colors flex items-center gap-2"
        >
          <Plus :size="16" />
          {{ $t('alerts.rules.create', 'Create Rule') }}
        </button>
      </div>

      <div class="p-4">
        <!-- Loading -->
        <div v-if="alertStore.isLoadingRules" class="space-y-3">
          <div v-for="i in 3" :key="i" class="h-16 bg-gray-700/50 rounded animate-pulse"></div>
        </div>

        <!-- Rules Table -->
        <AlertRuleTable
          v-else
          :rules="alertStore.rules"
          :loading="alertStore.isLoadingRules"
          @edit="openEditModal"
          @delete="handleDeleteRule"
          @toggle="handleToggleRule"
          @create="openCreateModal"
        />
      </div>
    </div>

    <!-- History Tab -->
    <div v-show="activeTab === 'history'" class="bg-gray-800 rounded-xl border border-gray-700">
      <div class="p-4 border-b border-gray-700">
        <h3 class="text-lg font-semibold text-white flex items-center gap-2">
          <History :size="20" class="text-purple-400" />
          {{ $t('alerts.history.title', 'Alert History') }}
        </h3>
      </div>

      <div class="p-4">
        <!-- Loading -->
        <div v-if="alertStore.isLoading" class="space-y-3">
          <div v-for="i in 5" :key="i" class="h-12 bg-gray-700/50 rounded animate-pulse"></div>
        </div>

        <!-- History Table -->
        <AlertHistoryTable
          v-else
          :history="alertStore.history"
          :pagination="alertStore.pagination"
          @page-change="handlePageChange"
        />
      </div>
    </div>

    <!-- Rule Edit Modal -->
    <AlertRuleEditModal
      :is-open="isModalOpen"
      :rule="editingRule"
      :loading="alertStore.isLoadingRules"
      @close="closeModal"
      @save="handleSaveRule"
    />

    <!-- Delete Confirmation -->
    <ConfirmDialog
      :is-open="isDeleteDialogOpen"
      :title="$t('alerts.delete.title', 'Delete Alert Rule')"
      :message="$t('alerts.delete.message', 'Are you sure you want to delete this alert rule? This action cannot be undone.')"
      :confirm-text="$t('common.delete', 'Delete')"
      confirm-variant="danger"
      @confirm="confirmDeleteRule"
      @cancel="isDeleteDialogOpen = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAlertStore } from '@/stores/alertStore'
import {
  AlertTriangle,
  RefreshCw,
  CheckCircle,
  Bell,
  Plus,
  Settings,
  History
} from 'lucide-vue-next'
import ActiveAlertCard from '@/components/alerts/ActiveAlertCard.vue'
import AlertRuleTable from '@/components/alerts/AlertRuleTable.vue'
import AlertRuleEditModal from '@/components/alerts/AlertRuleEditModal.vue'
import AlertHistoryTable from '@/components/alerts/AlertHistoryTable.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

const props = defineProps({
  timeRange: {
    type: String,
    default: '7d'
  }
})

const { t } = useI18n()
const alertStore = useAlertStore()

// Tab state
const activeTab = ref('rules')

// Modal state
const isModalOpen = ref(false)
const editingRule = ref(null)

// Delete dialog state
const isDeleteDialogOpen = ref(false)
const deletingRuleId = ref(null)

// Actions
async function refreshAlerts() {
  await alertStore.fetchActiveAlerts()
}

async function handleAcknowledge(alertId) {
  await alertStore.acknowledgeAlert(alertId)
}

async function handleMute(alertId) {
  await alertStore.muteAlert(alertId)
}

function openCreateModal() {
  editingRule.value = null
  isModalOpen.value = true
}

function openEditModal(rule) {
  editingRule.value = rule
  isModalOpen.value = true
}

function closeModal() {
  isModalOpen.value = false
  editingRule.value = null
}

async function handleSaveRule(ruleData) {
  let result
  if (ruleData.id) {
    result = await alertStore.updateRule(ruleData.id, ruleData)
  } else {
    result = await alertStore.createRule(ruleData)
  }

  if (result.ok) {
    closeModal()
  }
}

function handleDeleteRule(ruleId) {
  deletingRuleId.value = ruleId
  isDeleteDialogOpen.value = true
}

async function confirmDeleteRule() {
  if (deletingRuleId.value) {
    await alertStore.deleteRule(deletingRuleId.value)
    deletingRuleId.value = null
  }
  isDeleteDialogOpen.value = false
}

async function handleToggleRule(ruleId) {
  await alertStore.toggleRule(ruleId)
}

async function handlePageChange(page) {
  await alertStore.setPage(page)
}

// Load data on mount
onMounted(async () => {
  await Promise.all([
    alertStore.fetchActiveAlerts(),
    alertStore.fetchRules(),
    alertStore.fetchHistory()
  ])
})
</script>

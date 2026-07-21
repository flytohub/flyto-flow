<template>
  <div class="min-h-screen bg-gray-900">
    <div class="container mx-auto px-4 py-6">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-white flex items-center gap-3">
            <FileText :size="28" class="text-purple-400" />
            {{ $t('audit.title', 'Audit Logs') }}
          </h1>
          <p class="text-gray-400 mt-1">{{ $t('audit.description', 'Track all system activities and changes') }}</p>
        </div>
        <div class="flex items-center gap-3">
          <ChainVerificationStatus
            :verified="auditStore.isVerified"
            :is-verifying="auditStore.isVerifying"
            :last-verified-at="auditStore.lastVerifiedAt"
          />
          <button
            @click="verifyChain"
            :disabled="auditStore.isVerifying"
            class="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            <ShieldCheck :size="16" />
            {{ $t('audit.verifyChain', 'Verify Chain') }}
          </button>
          <AuditExportButton
            :loading="auditStore.isLoading"
            @export="handleExport"
          />
        </div>
      </div>

      <!-- Filters -->
      <div class="bg-gray-800 rounded-xl border border-gray-700 p-4 mb-6">
        <AuditLogFilter
          :filters="auditStore.filters"
          @update:filters="handleFiltersChange"
        />
      </div>

      <!-- Logs Table -->
      <div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
        <AuditLogTable
          :logs="auditStore.logs"
          :pagination="auditStore.pagination"
          :loading="auditStore.isLoading"
          @view-details="openLogDetail"
          @page-change="handlePageChange"
        />
      </div>

      <!-- Log Detail Slide-out -->
      <div
        class="fixed inset-0 z-50 transition-opacity"
        :class="selectedLog ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'"
      >
        <!-- Backdrop -->
        <div
          class="absolute inset-0 bg-black/50"
          @click="closeLogDetail"
        ></div>

        <!-- Panel -->
        <div
          class="absolute right-0 top-0 h-full w-full max-w-lg bg-gray-800 border-l border-gray-700 transform transition-transform"
          :class="selectedLog ? 'translate-x-0' : 'translate-x-full'"
        >
          <div class="p-4 border-b border-gray-700 flex items-center justify-between">
            <h3 class="text-lg font-semibold text-white">{{ $t('audit.detail.title', 'Log Details') }}</h3>
            <button
              @click="closeLogDetail"
              class="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
              aria-label="Close"
            >
              <X :size="20" />
            </button>
          </div>
          <div class="p-4 overflow-y-auto h-[calc(100%-64px)]">
            <AuditLogDetail v-if="selectedLog" :log="selectedLog" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuditStore } from '@/stores/auditStore'
import { FileText, ShieldCheck, X } from 'lucide-vue-next'
import AuditLogTable from '@/components/audit/AuditLogTable.vue'
import AuditLogFilter from '@/components/audit/AuditLogFilter.vue'
import AuditLogDetail from '@/components/audit/AuditLogDetail.vue'
import ChainVerificationStatus from '@/components/audit/ChainVerificationStatus.vue'
import AuditExportButton from '@/components/audit/AuditExportButton.vue'

const { t } = useI18n()
const auditStore = useAuditStore()

// Local state
const selectedLog = ref(null)

// Actions
async function handleFiltersChange(newFilters) {
  await auditStore.setFilters(newFilters)
}

async function handlePageChange(page) {
  await auditStore.setPage(page)
}

function openLogDetail(log) {
  selectedLog.value = log
}

function closeLogDetail() {
  selectedLog.value = null
}

async function verifyChain() {
  await auditStore.verifyChain()
}

async function handleExport(format) {
  const blob = await auditStore.exportLogs(format)
  if (blob) {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.${format}`
    a.click()
    URL.revokeObjectURL(url)
  }
}

// Load data on mount
onMounted(async () => {
  await auditStore.fetchLogs()
})
</script>

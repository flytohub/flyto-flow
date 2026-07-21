<template>
  <div class="space-y-6">
    <!-- Header Info -->
    <div class="grid grid-cols-2 gap-4">
      <div>
        <p class="text-xs text-gray-500 mb-1">{{ $t('audit.detail.sequence', 'Sequence #') }}</p>
        <p class="text-sm text-white font-mono">{{ log.sequenceNumber }}</p>
      </div>
      <div>
        <p class="text-xs text-gray-500 mb-1">{{ $t('audit.detail.timestamp', 'Timestamp') }}</p>
        <p class="text-sm text-white">{{ formatDateTime(log.timestamp) }}</p>
      </div>
      <div>
        <p class="text-xs text-gray-500 mb-1">{{ $t('audit.detail.actor', 'Actor') }}</p>
        <p class="text-sm text-white font-mono">{{ log.userId }}</p>
        <p class="text-xs text-gray-400">{{ log.userType }}</p>
      </div>
      <div>
        <p class="text-xs text-gray-500 mb-1">{{ $t('audit.detail.action', 'Action') }}</p>
        <ActionBadge :action="log.action" />
      </div>
    </div>

    <!-- Resource Info -->
    <div class="p-4 bg-gray-700/30 rounded-lg">
      <p class="text-xs text-gray-500 mb-2">{{ $t('audit.detail.resource', 'Resource') }}</p>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <p class="text-xs text-gray-400">{{ $t('audit.detail.resourceType', 'Type') }}</p>
          <p class="text-sm text-white">{{ log.resourceType }}</p>
        </div>
        <div>
          <p class="text-xs text-gray-400">{{ $t('audit.detail.resourceId', 'ID') }}</p>
          <p class="text-sm text-white font-mono break-all">{{ log.resourceId }}</p>
        </div>
      </div>
    </div>

    <!-- Client Info -->
    <div class="p-4 bg-gray-700/30 rounded-lg">
      <p class="text-xs text-gray-500 mb-2">{{ $t('audit.detail.clientInfo', 'Client Information') }}</p>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <p class="text-xs text-gray-400">{{ $t('audit.detail.ipAddress', 'IP Address') }}</p>
          <p class="text-sm text-white font-mono">{{ log.ipAddress || '-' }}</p>
        </div>
        <div class="col-span-2">
          <p class="text-xs text-gray-400">{{ $t('audit.detail.userAgent', 'User Agent') }}</p>
          <p class="text-sm text-white truncate">{{ log.userAgent || '-' }}</p>
        </div>
      </div>
    </div>

    <!-- Change Summary -->
    <div v-if="log.changeSummary" class="p-4 bg-gray-700/30 rounded-lg">
      <p class="text-xs text-gray-500 mb-2">{{ $t('audit.detail.changeSummary', 'Change Summary') }}</p>
      <p class="text-sm text-white">{{ log.changeSummary }}</p>
    </div>

    <!-- Value Hashes -->
    <div v-if="log.oldValueHash || log.newValueHash" class="p-4 bg-gray-700/30 rounded-lg">
      <p class="text-xs text-gray-500 mb-2">{{ $t('audit.detail.valueHashes', 'Value Hashes') }}</p>
      <div class="space-y-2">
        <div v-if="log.oldValueHash">
          <p class="text-xs text-gray-400">{{ $t('audit.detail.oldValueHash', 'Old Value') }}</p>
          <p class="text-xs text-white font-mono break-all">{{ log.oldValueHash }}</p>
        </div>
        <div v-if="log.newValueHash">
          <p class="text-xs text-gray-400">{{ $t('audit.detail.newValueHash', 'New Value') }}</p>
          <p class="text-xs text-white font-mono break-all">{{ log.newValueHash }}</p>
        </div>
      </div>
    </div>

    <!-- Chain Verification -->
    <div class="p-4 bg-gray-700/30 rounded-lg">
      <p class="text-xs text-gray-500 mb-2">{{ $t('audit.detail.chainInfo', 'Chain Information') }}</p>
      <div class="space-y-2">
        <div>
          <p class="text-xs text-gray-400">{{ $t('audit.detail.hash', 'Entry Hash') }}</p>
          <p class="text-xs text-white font-mono break-all">{{ log.hash || '-' }}</p>
        </div>
        <div>
          <p class="text-xs text-gray-400">{{ $t('audit.detail.prevHash', 'Previous Entry Hash') }}</p>
          <p class="text-xs text-white font-mono break-all">{{ log.prevHash || '-' }}</p>
        </div>
        <div v-if="log.traceId">
          <p class="text-xs text-gray-400">{{ $t('audit.detail.traceId', 'Trace ID') }}</p>
          <p class="text-xs text-white font-mono break-all">{{ log.traceId }}</p>
        </div>
      </div>
    </div>

    <!-- Metadata -->
    <div v-if="log.metadata && Object.keys(log.metadata).length > 0" class="p-4 bg-gray-700/30 rounded-lg">
      <p class="text-xs text-gray-500 mb-2">{{ $t('audit.detail.metadata', 'Metadata') }}</p>
      <pre class="text-xs text-white font-mono overflow-x-auto">{{ JSON.stringify(log.metadata, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup>
import ActionBadge from './ActionBadge.vue'

defineProps({
  log: {
    type: Object,
    required: true
  }
})

function formatDateTime(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}
</script>

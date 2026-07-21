<template>
  <div class="relative" ref="buttonContainerRef">
    <button
      ref="buttonRef"
      @click="togglePanel"
      class="relative flex items-center gap-2 px-3 py-2 rounded-lg transition-colors"
      :class="pendingCount > 0 ? 'bg-purple-600/20 text-purple-400 hover:bg-purple-600/30' : 'text-gray-400 hover:text-white hover:bg-gray-700'"
    >
      <Hand :size="18" />
      <span v-if="pendingCount > 0" class="text-sm font-medium">{{ pendingCount }}</span>

      <!-- Pulse animation when there are pending approvals -->
      <span
        v-if="pendingCount > 0"
        class="absolute -top-1 -right-1 flex h-3 w-3"
      >
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-3 w-3 bg-purple-500"></span>
      </span>
    </button>

    <!-- Dropdown Panel - Teleport to body -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition ease-out duration-200"
        enter-from-class="opacity-0 translate-y-1"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition ease-in duration-150"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 translate-y-1"
      >
        <div
          v-if="isPanelOpen"
          ref="dropdownRef"
          class="fixed w-80 bg-gray-800 border border-gray-700 rounded-xl shadow-xl overflow-hidden"
          :style="dropdownStyle"
        >
          <!-- Header -->
          <div class="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-purple-900/10">
            <span class="text-sm font-medium text-white">{{ $t('breakpoint.pendingApprovals') }}</span>
            <button
              @click="refreshBreakpoints"
              class="p-1 text-gray-400 hover:text-white transition-colors"
              :class="{ 'animate-spin': refreshing }"
            >
              <RefreshCw :size="14" />
            </button>
          </div>

          <!-- Loading -->
          <div v-if="loading" class="flex items-center justify-center py-8">
            <Loader :size="24" class="text-purple-400 animate-spin" />
          </div>

          <!-- List -->
          <div v-else-if="breakpoints.length" class="max-h-80 overflow-y-auto">
            <div
              v-for="bp in breakpoints"
              :key="bp.breakpointId"
              @click="selectBreakpoint(bp)"
              class="px-4 py-3 hover:bg-gray-700/50 cursor-pointer border-b border-gray-700/50 last:border-0"
            >
              <div class="flex items-start justify-between gap-2">
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-white truncate">{{ bp.title }}</p>
                  <p class="text-xs text-gray-400 truncate">{{ bp.workflowId || bp.stepId }}</p>
                </div>
                <div class="flex items-center gap-1">
                  <Clock :size="12" class="text-gray-500" />
                  <span class="text-xs text-gray-500">{{ formatTimeAgo(bp.createdAt) }}</span>
                </div>
              </div>
              <div v-if="bp.expiresAt" class="mt-1 flex items-center gap-1">
                <AlertTriangle v-if="isExpiringSoon(bp.expiresAt)" :size="12" class="text-yellow-400" />
                <span class="text-xs" :class="isExpiringSoon(bp.expiresAt) ? 'text-yellow-400' : 'text-gray-500'">
                  {{ formatTimeRemaining(bp.expiresAt) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div v-else class="flex flex-col items-center justify-center py-8 text-gray-400">
            <CheckCircle :size="32" class="mb-2 opacity-50" />
            <p class="text-sm">{{ $t('breakpoint.noPending') }}</p>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Browser Interact Dialog (for browser.interact breakpoints) -->
    <BrowserInteractDialog
      v-if="isInteractBreakpoint"
      :is-open="selectedBreakpoint !== null"
      :breakpoint="selectedBreakpoint"
      :user-id="userId"
      @close="selectedBreakpoint = null"
      @approve="handleApprove"
      @reject="handleReject"
    />

    <!-- Standard Approval Modal (for flow.breakpoint) -->
    <BreakpointApprovalPanel
      v-else
      :is-open="selectedBreakpoint !== null"
      :breakpoint="selectedBreakpoint"
      :user-id="userId"
      @close="selectedBreakpoint = null"
      @approve="handleApprove"
      @reject="handleReject"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Hand,
  RefreshCw,
  Loader,
  Clock,
  AlertTriangle,
  CheckCircle
} from 'lucide-vue-next'
import BreakpointApprovalPanel from './BreakpointApprovalPanel.vue'
import { get, post } from '@/api/client'
import BrowserInteractDialog from './BrowserInteractDialog.vue'

const props = defineProps({
  userId: {
    type: String,
    default: 'current_user'
  },
  pollInterval: {
    type: Number,
    default: 3000 // 3 seconds (fast enough for interact dialogs)
  }
})

const emit = defineEmits(['approved', 'rejected'])
const { t } = useI18n()

const buttonRef = ref(null)
const buttonContainerRef = ref(null)
const dropdownRef = ref(null)
const isPanelOpen = ref(false)
const loading = ref(false)
const refreshing = ref(false)
const breakpoints = ref([])
const selectedBreakpoint = ref(null)
const dropdownPosition = ref({ top: 0, right: 0 })
let pollTimer = null

const pendingCount = computed(() => breakpoints.value.length)

// Detect if the selected breakpoint is a browser.interact type
const isInteractBreakpoint = computed(() => {
  const bp = selectedBreakpoint.value
  if (!bp) return false
  const ctx = bp.contextSnapshot || bp.context_snapshot || {}
  return ctx._interact === true
})

const dropdownStyle = computed(() => ({
  top: `${dropdownPosition.value.top}px`,
  right: `${dropdownPosition.value.right}px`,
  zIndex: 1100
}))

function updateDropdownPosition() {
  if (!buttonRef.value) return

  const rect = buttonRef.value.getBoundingClientRect()
  dropdownPosition.value = {
    top: rect.bottom + 8, // 8px gap below button
    right: window.innerWidth - rect.right
  }
}

watch(isPanelOpen, async (newVal) => {
  if (newVal) {
    await nextTick()
    updateDropdownPosition()
  }
})

onMounted(() => {
  fetchBreakpoints()
  // Start polling
  pollTimer = setInterval(fetchBreakpoints, props.pollInterval)

  // Update position on scroll/resize
  window.addEventListener('scroll', updateDropdownPosition, true)
  window.addEventListener('resize', updateDropdownPosition)

  // Close on click outside
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
  }
  window.removeEventListener('scroll', updateDropdownPosition, true)
  window.removeEventListener('resize', updateDropdownPosition)
  document.removeEventListener('click', handleClickOutside)
})

function handleClickOutside(event) {
  if (!isPanelOpen.value) return

  const clickedButton = buttonContainerRef.value?.contains(event.target)
  const clickedDropdown = dropdownRef.value?.contains(event.target)

  if (!clickedButton && !clickedDropdown) {
    isPanelOpen.value = false
  }
}

function togglePanel() {
  isPanelOpen.value = !isPanelOpen.value
  if (isPanelOpen.value) {
    fetchBreakpoints()
  }
}

async function fetchBreakpoints() {
  try {
    const data = await get('/breakpoints/pending')
    if (data && !data.error) {
      breakpoints.value = data.breakpoints || []

      // Auto-close dialog if the selected breakpoint is no longer pending
      if (selectedBreakpoint.value) {
        const bpId = selectedBreakpoint.value.breakpointId || selectedBreakpoint.value.breakpoint_id
        const stillPending = breakpoints.value.some(bp =>
          (bp.breakpointId || bp.breakpoint_id) === bpId
        )
        if (!stillPending) {
          selectedBreakpoint.value = null
        }
      }

      // Auto-open dialog for browser.interact breakpoints
      if (!selectedBreakpoint.value && breakpoints.value.length > 0) {
        const interactBp = breakpoints.value.find(bp => {
          const ctx = bp.contextSnapshot || bp.context_snapshot || {}
          return ctx._interact === true
        })
        if (interactBp) {
          selectedBreakpoint.value = interactBp
        }
      }
    }
  } catch (e) {
  }
}

async function refreshBreakpoints() {
  refreshing.value = true
  await fetchBreakpoints()
  setTimeout(() => {
    refreshing.value = false
  }, 500)
}

function selectBreakpoint(bp) {
  selectedBreakpoint.value = bp
  isPanelOpen.value = false
}

async function handleApprove(data) {
  const bpId = data.breakpointId || data.breakpoint_id
  if (!bpId) return
  try {
    const result = await post(`/breakpoints/${bpId}/respond`, {
      approved: true,
      comment: data.comment || '',
      custom_inputs: data.customInputs || data.custom_inputs || {}
    })

    if (result && !result.error) {
      emit('approved', result)
      selectedBreakpoint.value = null
      fetchBreakpoints()
    }
  } catch (e) {
  }
}

async function handleReject(data) {
  const bpId = data.breakpointId || data.breakpoint_id
  if (!bpId) return
  try {
    const result = await post(`/breakpoints/${bpId}/respond`, {
      approved: false,
      comment: data.comment || ''
    })

    if (result && !result.error) {
      emit('rejected', result)
      selectedBreakpoint.value = null
      fetchBreakpoints()
    }
  } catch (e) {
  }
}

function formatTimeAgo(timestamp) {
  const seconds = Math.floor((new Date() - new Date(timestamp)) / 1000)

  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

function formatTimeRemaining(expiresAt) {
  const remaining = new Date(expiresAt) - new Date()
  if (remaining <= 0) return 'Expired'

  const minutes = Math.floor(remaining / 60000)
  if (minutes < 60) return `${minutes}m left`
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m left`
}

function isExpiringSoon(expiresAt) {
  const remaining = new Date(expiresAt) - new Date()
  return remaining < 5 * 60 * 1000 // Less than 5 minutes
}
</script>

<template>
  <!--
    Global Browser Interact Overlay
    Appears on any page when a browser.interact breakpoint is pending.
    Triggered by WebSocket push from backend.
  -->
  <BrowserInteractDialog
    v-if="showDialog"
    :is-open="showDialog"
    :breakpoint="currentBreakpoint"
    @close="handleClose"
    @approve="handleApprove"
    @reject="handleReject"
  />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { post } from '@/api/client'
import BrowserInteractDialog from './BrowserInteractDialog.vue'
import { useGlobalInteract } from '../../composables/useBreakpointWS'

const { pendingInteract, clearInteract } = useGlobalInteract()

const dismissed = ref(false)

// Also listen for the custom event (fallback for non-WS mode)
const eventBreakpoint = ref(null)

function onInteractEvent(e) {
  eventBreakpoint.value = e.detail
  dismissed.value = false
}

onMounted(() => {
  window.addEventListener('flyto-interact-breakpoint', onInteractEvent)

})

onUnmounted(() => {
  window.removeEventListener('flyto-interact-breakpoint', onInteractEvent)
})

const currentBreakpoint = computed(() => {
  return pendingInteract.value || eventBreakpoint.value
})

const showDialog = computed(() => {
  return !dismissed.value && currentBreakpoint.value !== null
})

function handleClose() {
  dismissed.value = true
  clearInteract()
  eventBreakpoint.value = null
}

async function handleApprove(data) {
  const bpId = data.breakpointId || data.breakpoint_id
  if (!bpId) return

  try {
    const result = await post(`/breakpoints/${bpId}/respond`, {
      approved: true,
      comment: data.comment || '',
      custom_inputs: data.customInputs || data.custom_inputs || {},
    })

    if (result && !result.error) {
      clearInteract()
      eventBreakpoint.value = null
      dismissed.value = false
    }
  } catch (e) {
    console.error('Failed to approve breakpoint:', e)
  }
}

async function handleReject(data) {
  const bpId = data.breakpointId || data.breakpoint_id
  if (!bpId) return

  try {
    const result = await post(`/breakpoints/${bpId}/respond`, {
      approved: false,
      comment: data.comment || 'Skipped locally',
    })

    if (result && !result.error) {
      clearInteract()
      eventBreakpoint.value = null
      dismissed.value = false
    }
  } catch (e) {
    console.error('Failed to reject breakpoint:', e)
  }
}
</script>

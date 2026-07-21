<template>
  <div class="bg-gray-900 rounded-lg border border-gray-700 p-4 space-y-3">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-2">
        <Webhook :size="16" class="text-amber-400" />
        <span class="text-sm font-medium text-white">{{ $t('triggers.webhookTest', 'Test Webhook') }}</span>
      </div>
      <button @click="$emit('close')" aria-label="Close" class="p-1 text-gray-400 hover:text-white">
        <X :size="16" />
      </button>
    </div>

    <!-- Not started -->
    <template v-if="state === 'idle'">
      <p class="text-xs text-gray-400">
        {{ $t('triggers.webhookTestDesc', 'Start a 30-second test listener, then send a request to the URL below.') }}
      </p>
      <button
        @click="startTest"
        class="w-full px-3 py-2 bg-amber-600 hover:bg-amber-700 text-white text-sm rounded-lg transition-colors"
      >
        {{ $t('triggers.startTest', 'Start Test') }}
      </button>
    </template>

    <!-- Listening -->
    <template v-else-if="state === 'listening'">
      <!-- Trigger URL -->
      <div>
        <label class="block text-xs text-gray-500 mb-1">Trigger URL</label>
        <div class="flex items-center gap-2">
          <code class="flex-1 text-xs text-green-400 bg-gray-800 px-2 py-1.5 rounded overflow-x-auto">
            {{ triggerUrl }}
          </code>
          <button @click="copyUrl" aria-label="Copy URL" class="p-1.5 text-gray-400 hover:text-white transition-colors">
            <Copy :size="14" />
          </button>
        </div>
      </div>

      <!-- cURL example -->
      <div>
        <label class="block text-xs text-gray-500 mb-1">cURL</label>
        <div class="flex items-center gap-2">
          <code class="flex-1 text-xs text-gray-300 bg-gray-800 px-2 py-1.5 rounded overflow-x-auto whitespace-nowrap">
            {{ curlExample }}
          </code>
          <button @click="copyCurl" aria-label="Copy cURL" class="p-1.5 text-gray-400 hover:text-white transition-colors">
            <Copy :size="14" />
          </button>
        </div>
      </div>

      <!-- Waiting indicator -->
      <div class="flex items-center gap-2 py-2">
        <Loader :size="14" class="text-amber-400 animate-spin" />
        <span class="text-xs text-amber-400">
          {{ $t('triggers.waitingPayload', 'Waiting for payload...') }}
          <span class="text-gray-500">({{ remainingSeconds }}s)</span>
        </span>
      </div>
    </template>

    <!-- Received -->
    <template v-else-if="state === 'received'">
      <div class="flex items-center gap-2 mb-2">
        <CheckCircle :size="14" class="text-green-400" />
        <span class="text-xs text-green-400">{{ $t('triggers.payloadReceived', 'Payload received!') }}</span>
      </div>
      <div class="bg-gray-800 rounded p-2 max-h-48 overflow-y-auto">
        <pre class="text-xs text-gray-300 whitespace-pre-wrap">{{ JSON.stringify(receivedPayload, null, 2) }}</pre>
      </div>
      <button
        @click="resetTest"
        class="w-full px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded-lg"
      >
        {{ $t('triggers.testAgain', 'Test Again') }}
      </button>
    </template>

    <!-- Timeout -->
    <template v-else-if="state === 'timeout'">
      <div class="flex items-center gap-2">
        <Clock :size="14" class="text-gray-400" />
        <span class="text-xs text-gray-400">{{ $t('triggers.testTimeout', 'Test timed out. No payload received in 30 seconds.') }}</span>
      </div>
      <button
        @click="resetTest"
        class="w-full px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded-lg"
      >
        {{ $t('triggers.tryAgain', 'Try Again') }}
      </button>
    </template>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { Webhook, X, Copy, Loader, CheckCircle, Clock } from 'lucide-vue-next'
import { startWebhookTest, getWebhookTestResult } from '@/api/triggers'

const props = defineProps({
  webhookId: { type: String, required: true }
})

defineEmits(['close'])

const state = ref('idle') // idle | listening | received | timeout
const triggerUrl = ref('')
const curlExample = ref('')
const receivedPayload = ref(null)
const remainingSeconds = ref(30)
let countdownTimer = null

async function startTest() {
  const result = await startWebhookTest(props.webhookId)
  if (!result.ok) return

  triggerUrl.value = `${window.location.origin}${result.trigger_url}`
  curlExample.value = result.curl_example.replace('http://localhost:8000', window.location.origin)
  state.value = 'listening'
  remainingSeconds.value = 30

  // Countdown timer
  countdownTimer = setInterval(() => {
    remainingSeconds.value--
    if (remainingSeconds.value <= 0) {
      clearInterval(countdownTimer)
    }
  }, 1000)

  // Long-poll for result
  const response = await getWebhookTestResult(props.webhookId)
  clearInterval(countdownTimer)

  if (response.ok && response.received) {
    receivedPayload.value = response.payload
    state.value = 'received'
  } else {
    state.value = 'timeout'
  }
}

function resetTest() {
  state.value = 'idle'
  triggerUrl.value = ''
  curlExample.value = ''
  receivedPayload.value = null
  remainingSeconds.value = 30
}

async function copyUrl() {
  await navigator.clipboard.writeText(triggerUrl.value)
}

async function copyCurl() {
  await navigator.clipboard.writeText(curlExample.value)
}

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>

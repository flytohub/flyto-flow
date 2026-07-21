<template>
  <div class="trigger-config-panel space-y-4">
    <!-- Trigger Type Selector -->
    <div>
      <label class="block text-xs text-gray-500 mb-2">{{ $t('triggers.triggerType', 'Trigger Type') }}</label>
      <div class="flex gap-2">
        <button
          v-for="opt in triggerTypes"
          :key="opt.value"
          @click="updateParam('trigger_type', opt.value)"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border transition-colors"
          :class="currentType === opt.value
            ? 'border-amber-500 bg-amber-600/20 text-amber-300'
            : 'border-gray-600 text-gray-400 hover:border-gray-500'"
        >
          <component :is="opt.icon" :size="14" />
          {{ opt.label }}
        </button>
      </div>
    </div>

    <!-- MCP Config -->
    <template v-if="currentType === 'mcp'">
      <div>
        <label class="block text-xs text-gray-500 mb-1">Tool Name</label>
        <input
          :value="params.tool_name || ''"
          @input="updateParam('tool_name', $event.target.value)"
          class="w-full bg-gray-900 border border-gray-600 text-sm text-white px-3 py-1.5 rounded-lg focus:border-amber-500 focus:outline-none"
          placeholder="run_project_smoke"
        />
      </div>

      <div>
        <label class="block text-xs text-gray-500 mb-1">Description</label>
        <input
          :value="params.tool_description || ''"
          @input="updateParam('tool_description', $event.target.value)"
          class="w-full bg-gray-900 border border-gray-600 text-sm text-white px-3 py-1.5 rounded-lg focus:border-amber-500 focus:outline-none"
          placeholder="Run project smoke"
        />
      </div>
    </template>

    <!-- Schedule Config -->
    <template v-if="currentType === 'schedule'">
      <div>
        <label class="block text-xs text-gray-500 mb-1">Cron Expression</label>
        <div class="flex gap-2">
          <input
            :value="params.cron_expression || ''"
            @input="updateParam('cron_expression', $event.target.value)"
            class="flex-1 bg-gray-900 border border-gray-600 text-sm text-white px-3 py-1.5 rounded-lg focus:border-amber-500 focus:outline-none"
            placeholder="0 9 * * *"
          />
          <button
            @click="validateCronExpression"
            class="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-xs text-gray-300 rounded-lg"
          >
            {{ $t('triggers.validate', 'Validate') }}
          </button>
        </div>
        <p v-if="cronError" class="text-xs text-red-400 mt-1">{{ cronError }}</p>
      </div>

      <!-- Timezone -->
      <div>
        <label class="block text-xs text-gray-500 mb-1">{{ $t('triggers.timezone', 'Timezone') }}</label>
        <select
          :value="params.timezone || 'UTC'"
          @change="updateParam('timezone', $event.target.value)"
          class="w-full bg-gray-900 border border-gray-600 text-sm text-white px-3 py-1.5 rounded-lg focus:border-amber-500 focus:outline-none"
        >
          <option v-for="tz in commonTimezones" :key="tz" :value="tz">{{ tz }}</option>
        </select>
      </div>

      <!-- Next Run Preview -->
      <div v-if="nextRuns.length" class="bg-gray-900/50 rounded-lg p-3">
        <label class="block text-xs text-gray-500 mb-2">{{ $t('triggers.nextRuns', 'Next Runs') }}</label>
        <div class="space-y-1">
          <div v-for="(run, i) in nextRuns" :key="i" class="flex items-center gap-2 text-xs">
            <Clock :size="12" class="text-amber-400" />
            <span class="text-gray-300">{{ formatDate(run) }}</span>
          </div>
        </div>
      </div>

      <!-- Quick Presets -->
      <div>
        <label class="block text-xs text-gray-500 mb-1">{{ $t('triggers.presets', 'Quick Presets') }}</label>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="preset in cronPresets"
            :key="preset.cron"
            @click="updateParam('cron_expression', preset.cron)"
            class="px-2 py-1 text-xs bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-gray-200 rounded border border-gray-700 transition-colors"
          >
            {{ preset.label }}
          </button>
        </div>
      </div>
    </template>

    <!-- Webhook Config -->
    <template v-if="currentType === 'webhook'">
      <!-- Webhook URL -->
      <div v-if="params.webhook_url">
        <label class="block text-xs text-gray-500 mb-1">Webhook URL</label>
        <div class="flex items-center gap-2">
          <code class="flex-1 text-xs text-green-400 bg-gray-900 px-2 py-1.5 rounded overflow-x-auto">
            {{ params.webhook_url }}
          </code>
          <button @click="copyToClipboard(params.webhook_url)" aria-label="Copy URL" class="p-1.5 text-gray-400 hover:text-white">
            <Copy :size="14" />
          </button>
        </div>
      </div>

      <!-- Provider -->
      <div>
        <label class="block text-xs text-gray-500 mb-1">{{ $t('triggers.provider', 'Provider') }}</label>
        <div class="flex gap-2">
          <button
            v-for="prov in webhookProviders"
            :key="prov.value"
            @click="updateParam('webhook_provider', prov.value)"
            class="px-3 py-1.5 text-xs rounded-lg border transition-colors"
            :class="(params.webhook_provider || 'generic') === prov.value
              ? 'border-amber-500 bg-amber-600/20 text-amber-300'
              : 'border-gray-600 text-gray-400 hover:border-gray-500'"
          >
            {{ prov.label }}
          </button>
        </div>
      </div>

      <!-- Signature Required -->
      <div class="flex items-center gap-2">
        <input
          type="checkbox"
          :checked="params.require_signature !== false"
          @change="updateParam('require_signature', $event.target.checked)"
          class="rounded bg-gray-900 border-gray-600 text-amber-500 focus:ring-amber-500"
        />
        <label class="text-xs text-gray-400">{{ $t('triggers.requireSignature', 'Require Signature Verification') }}</label>
      </div>

      <!-- Test Button -->
      <button
        v-if="webhookId"
        @click="$emit('test-webhook', webhookId)"
        class="w-full px-3 py-2 bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 text-xs rounded-lg border border-amber-600/30 transition-colors flex items-center justify-center gap-2"
      >
        <Play :size="14" />
        {{ $t('triggers.testWebhook', 'Test Webhook') }}
      </button>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Hand, Webhook, Clock, Radio, Copy, Play, PlugZap } from 'lucide-vue-next'
import { validateCron } from '@/api/triggers'

const props = defineProps({
  params: { type: Object, default: () => ({}) },
  webhookId: { type: String, default: null },
  readOnly: { type: Boolean, default: false },
})

const emit = defineEmits(['update:params', 'test-webhook'])

const cronError = ref('')
const nextRuns = ref([])

const currentType = computed(() => props.params.trigger_type || 'manual')

const triggerTypes = [
  { value: 'manual', label: 'Manual', icon: Hand },
  { value: 'webhook', label: 'Webhook', icon: Webhook },
  { value: 'schedule', label: 'Schedule', icon: Clock },
  { value: 'event', label: 'Event', icon: Radio },
  { value: 'mcp', label: 'MCP', icon: PlugZap },
]

const webhookProviders = [
  { value: 'generic', label: 'Generic' },
  { value: 'github', label: 'GitHub' },
  { value: 'stripe', label: 'Stripe' },
  { value: 'slack', label: 'Slack' },
]

const cronPresets = [
  { label: 'Every 15 min', cron: '*/15 * * * *' },
  { label: 'Hourly', cron: '0 * * * *' },
  { label: 'Daily 9 AM', cron: '0 9 * * *' },
  { label: 'Weekly Mon', cron: '0 9 * * 1' },
  { label: 'Monthly', cron: '0 0 1 * *' },
]

const commonTimezones = [
  'UTC',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Berlin',
  'Europe/Paris',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Asia/Taipei',
  'Asia/Seoul',
  'Asia/Kolkata',
  'Asia/Singapore',
  'Australia/Sydney',
  'Pacific/Auckland',
]

function updateParam(key, value) {
  emit('update:params', { ...props.params, [key]: value })
}

async function validateCronExpression() {
  const expr = props.params.cron_expression
  if (!expr) {
    cronError.value = 'Expression required'
    return
  }

  const result = await validateCron(expr)
  if (result.ok && result.valid) {
    cronError.value = ''
    // Fetch next runs
    fetchNextRuns()
  } else {
    cronError.value = result.error || 'Invalid expression'
    nextRuns.value = []
  }
}

async function fetchNextRuns() {
  const expr = props.params.cron_expression
  const tz = props.params.timezone || 'UTC'
  if (!expr) return

  try {
    const { get } = await import('@/api/client')
    const result = await get(`/triggers/cron/next?expression=${encodeURIComponent(expr)}&timezone=${encodeURIComponent(tz)}&count=3`)
    if (result.ok) {
      nextRuns.value = result.next_runs || []
    }
  } catch {
    // Non-critical
  }
}

function formatDate(iso) {
  return new Date(iso).toLocaleString()
}

async function copyToClipboard(text) {
  await navigator.clipboard.writeText(text)
}

// Auto-fetch next runs when cron changes
watch(() => props.params.cron_expression, (val) => {
  if (val && val.split(' ').length === 5) {
    fetchNextRuns()
  }
})
</script>

<style scoped>
.trigger-config-panel {
  padding: 8px 0;
}
</style>

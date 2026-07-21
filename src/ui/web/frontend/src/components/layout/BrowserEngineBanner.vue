<template>
  <!-- Renders nothing when the engine is ready (or dismissed during provisioning). -->
  <Transition name="be-banner">
    <div
      v-if="showBanner"
      class="w-full px-4 py-2 sm:px-6"
      :class="isDegraded
        ? 'bg-amber-50 dark:bg-amber-900/30 border-b border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200'
        : 'bg-blue-50 dark:bg-blue-900/30 border-b border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-200'"
      role="status"
      aria-live="polite"
    >
      <div class="container mx-auto flex items-center gap-3">
        <!-- Icon -->
        <component
          :is="isDegraded ? AlertTriangle : Download"
          :size="18"
          class="flex-shrink-0"
          :class="isDegraded ? '' : 'animate-pulse'"
        />

        <!-- Message + progress -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-sm font-medium">
              {{ isDegraded ? t('browserEngine.degradedTitle') : t('browserEngine.provisioningTitle') }}
            </span>
            <span class="text-xs opacity-80">
              {{ isDegraded ? errorReason : t('browserEngine.provisioningHint') }}
            </span>
          </div>

          <!-- Progress bar (provisioning only) -->
          <div v-if="!isDegraded" class="mt-1.5 flex items-center gap-2">
            <div class="flex-1 h-1.5 rounded-full bg-blue-200/60 dark:bg-blue-800/60 overflow-hidden">
              <div
                class="h-full rounded-full bg-blue-500 dark:bg-blue-400 transition-all duration-500 ease-out"
                :class="{ 'animate-pulse w-1/3': percent === null }"
                :style="percent !== null ? { width: percent + '%' } : {}"
              />
            </div>
            <span v-if="percent !== null" class="text-xs font-medium tabular-nums w-9 text-right">
              {{ percent }}%
            </span>
          </div>

          <!-- Per-component sub-status (provisioning only, when useful) -->
          <div
            v-if="!isDegraded && (nodeLabel || chromiumLabel)"
            class="mt-1 flex items-center gap-3 text-[11px] opacity-70"
          >
            <span v-if="nodeLabel">Node: {{ nodeLabel }}</span>
            <span v-if="chromiumLabel">Chromium: {{ chromiumLabel }}</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex-shrink-0 flex items-center gap-2">
          <button
            v-if="isDegraded"
            type="button"
            class="px-3 py-1 text-sm font-medium rounded-md bg-amber-600 hover:bg-amber-700 text-white transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            :disabled="retrying"
            @click="retry"
          >
            {{ retrying ? t('browserEngine.retrying') : t('browserEngine.retry') }}
          </button>
          <button
            v-else
            type="button"
            class="p-1 rounded hover:bg-blue-200/50 dark:hover:bg-blue-800/50 transition-colors"
            :aria-label="t('common.dismiss')"
            @click="dismissed = true"
          >
            <X :size="16" />
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Download, AlertTriangle, X } from 'lucide-vue-next'
import { useBrowserEngine } from '@/composables/useBrowserEngine'

const { t } = useI18n()
const { state, node, chromium, error, percent, retrying, retry } = useBrowserEngine()

// Dismiss only applies to the (non-blocking) provisioning banner. Degraded
// stays until the engine recovers.
const dismissed = ref(false)

const isDegraded = computed(() => state.value === 'degraded')

const isProvisioning = computed(
  () => state.value === 'provisioning' || state.value === 'pending'
)

const showBanner = computed(() => {
  if (isDegraded.value) return true
  if (isProvisioning.value) return !dismissed.value
  return false // ready (or any other state) → render nothing
})

const errorReason = computed(() => error.value || t('browserEngine.degradedFallback'))

function componentLabel(comp) {
  if (!comp || !comp.state) return ''
  if (comp.state === 'ready') return t('browserEngine.compReady')
  if (typeof comp.progress === 'number') return `${Math.round(comp.progress)}%`
  return t('browserEngine.compWorking')
}

const nodeLabel = computed(() => componentLabel(node.value))
const chromiumLabel = computed(() => componentLabel(chromium.value))
</script>

<style scoped>
.be-banner-enter-active,
.be-banner-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.be-banner-enter-from,
.be-banner-leave-to {
  opacity: 0;
  transform: translateY(-100%);
}
</style>

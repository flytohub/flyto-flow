<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <!-- Backdrop -->
        <div
          class="absolute inset-0 bg-black/60 backdrop-blur-sm"
          @click="$emit('update:modelValue', false)"
        />

        <!-- Modal -->
        <Transition
          enter-active-class="transition ease-out duration-200"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition ease-in duration-150"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="modelValue"
            class="relative w-full max-w-md bg-gray-900 rounded-2xl shadow-2xl border border-gray-700/50 overflow-hidden"
          >
            <!-- Gradient Header -->
            <div class="bg-gradient-to-r from-amber-600 via-orange-500 to-amber-600 p-6 text-center">
              <div class="w-16 h-16 mx-auto bg-white/20 rounded-full flex items-center justify-center mb-4">
                <Lock :size="32" class="text-white" />
              </div>
              <h3 class="text-xl font-bold text-white">{{ $t('upgrade.title') }}</h3>
              <p class="text-amber-100 mt-1 text-sm">{{ $t('upgrade.subtitle') }}</p>
            </div>

            <!-- Content -->
            <div class="p-6">
              <!-- Feature description -->
              <p class="text-gray-400 text-center mb-6">
                {{ featureDescription || $t('upgrade.debugFeatures') }}
              </p>

              <!-- Features list -->
              <div class="space-y-3 mb-6">
                <div
                  v-for="feature in features"
                  :key="feature"
                  class="flex items-center gap-3 text-sm text-gray-300"
                >
                  <CheckCircle :size="18" class="text-green-400 flex-shrink-0" />
                  <span>{{ feature }}</span>
                </div>
              </div>

              <!-- Pricing options -->
              <div class="space-y-3">
                <!-- Subscription -->
                <button
                  @click="handleSubscription"
                  class="w-full py-3 px-4 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-white font-semibold rounded-xl transition-all duration-200 flex items-center justify-center gap-2"
                >
                  <Zap :size="18" />
                  {{ $t('upgrade.subscription') }}
                </button>

                <!-- Offline License -->
                <button
                  @click="handleOfflineLicense"
                  class="w-full py-3 px-4 bg-gray-800 hover:bg-gray-700 text-gray-200 font-medium rounded-xl border border-gray-600 transition-all duration-200 flex items-center justify-center gap-2"
                >
                  <Download :size="18" />
                  {{ $t('upgrade.offlineLicense') }}
                </button>
              </div>

              <!-- Enterprise link -->
              <p class="text-center text-gray-500 text-xs mt-4">
                {{ $t('upgrade.enterpriseHint') }}
                <a href="mailto:sales@flyto2.com" class="text-amber-400 hover:text-amber-300">
                  {{ $t('upgrade.contactSales') }}
                </a>
              </p>
            </div>

            <!-- Close button -->
            <button
              @click="$emit('update:modelValue', false)"
              class="absolute top-4 right-4 p-2 text-white/70 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
              aria-label="Close"
            >
              <X :size="20" />
            </button>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Lock,
  CheckCircle,
  Zap,
  Download,
  X
} from 'lucide-vue-next'
import { telemetry } from '@/services/telemetry'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  featureDescription: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])
const router = useRouter()
const { t } = useI18n()

const features = computed(() => [
  t('upgrade.features.evidence'),
  t('upgrade.features.lineage'),
  t('upgrade.features.replay'),
  t('upgrade.features.tests'),
  t('upgrade.features.versions')
])

function handleSubscription() {
  emit('update:modelValue', false)

  // Track upgrade click
  telemetry.track('subscription.upgrade_click', {
    type: 'subscription',
    source: 'upgrade_modal'
  })

  router.push('/pricing')
}

function handleOfflineLicense() {
  emit('update:modelValue', false)

  // Track upgrade click
  telemetry.track('subscription.upgrade_click', {
    type: 'offline_license',
    source: 'upgrade_modal'
  })

  router.push('/pricing?type=offline')
}
</script>

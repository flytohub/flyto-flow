<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      role="dialog"
      aria-modal="true"
      aria-labelledby="publish-template-modal-title"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      @keydown.esc="close"
    >
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-black/50 backdrop-blur-sm"
        @click="close"
      ></div>

      <!-- Modal -->
      <div class="relative w-full max-w-lg bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 id="publish-template-modal-title" class="text-xl font-bold text-gray-900 dark:text-white">{{ $t('publish.title') }}</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {{ template?.name || template?.template_name }}
            </p>
          </div>
          <button
            @click="close"
            :aria-label="t('accessibility.closeDialog')"
            class="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
          >
            <X :size="20" aria-hidden="true" />
          </button>
        </div>

        <!-- Body -->
        <form @submit.prevent="submit" class="flex-1 overflow-y-auto p-6 space-y-6">
          <!-- Visibility -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              {{ $t('publish.visibility.label') }}
            </label>
            <div class="grid grid-cols-2 gap-3">
              <button
                v-for="option in visibilityOptions"
                :key="option.value"
                type="button"
                @click="form.visibility = option.value"
                :class="[
                  'p-4 rounded-xl border-2 text-left transition-all',
                  form.visibility === option.value
                    ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                ]"
              >
                <div class="flex items-center gap-2 mb-1">
                  <component
                    :is="option.value === 'public' ? Globe : Lock"
                    :size="16"
                    :class="form.visibility === option.value ? 'text-purple-600' : 'text-gray-500'"
                  />
                  <span :class="[
                    'font-medium',
                    form.visibility === option.value ? 'text-purple-600' : 'text-gray-900 dark:text-white'
                  ]">
                    {{ option.label }}
                  </span>
                </div>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {{ option.description }}
                </p>
              </button>
            </div>
          </div>

          <!-- Protection (Mutability) -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              {{ $t('publish.protection.label') }}
            </label>
            <div class="grid grid-cols-2 gap-3">
              <button
                v-for="option in mutabilityOptions"
                :key="option.value"
                type="button"
                @click="form.mutability = option.value"
                :class="[
                  'p-4 rounded-xl border-2 text-left transition-all',
                  form.mutability === option.value
                    ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                ]"
              >
                <div class="flex items-center gap-2 mb-1">
                  <component
                    :is="option.value === 'locked' ? Shield : GitFork"
                    :size="16"
                    :class="form.mutability === option.value ? 'text-purple-600' : 'text-gray-500'"
                  />
                  <span :class="[
                    'font-medium',
                    form.mutability === option.value ? 'text-purple-600' : 'text-gray-900 dark:text-white'
                  ]">
                    {{ option.label }}
                  </span>
                </div>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {{ option.description }}
                </p>
              </button>
            </div>
          </div>

          <!-- Pricing -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              {{ $t('publish.pricing.label') }}
            </label>
            <div class="grid grid-cols-2 gap-3 mb-4">
              <button
                v-for="option in pricingOptions"
                :key="option.value"
                type="button"
                @click="form.pricing = option.value"
                :class="[
                  'p-4 rounded-xl border-2 text-left transition-all',
                  form.pricing === option.value
                    ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                ]"
              >
                <div class="flex items-center gap-2 mb-1">
                  <component
                    :is="option.value === 'free' ? Gift : DollarSign"
                    :size="16"
                    :class="form.pricing === option.value ? 'text-purple-600' : 'text-gray-500'"
                  />
                  <span :class="[
                    'font-medium',
                    form.pricing === option.value ? 'text-purple-600' : 'text-gray-900 dark:text-white'
                  ]">
                    {{ option.label }}
                  </span>
                </div>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {{ option.description }}
                </p>
              </button>
            </div>

            <!-- Price input (if paid) -->
            <div v-if="form.pricing === 'paid'" class="space-y-3">
              <div class="flex gap-3">
                <div class="flex-1">
                  <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">{{ $t('publish.pricing.price') }}</label>
                  <div class="relative">
                    <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">$</span>
                    <input
                      v-model.number="priceDisplay"
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="9.99"
                      class="w-full pl-7 pr-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                </div>
                <div class="w-24">
                  <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">{{ $t('publish.pricing.currency') }}</label>
                  <AppSelect
                    v-model="form.currency"
                    :options="currencies.map(c => ({ value: c.value, label: c.value }))"
                  />
                </div>
              </div>

              <!-- Fee breakdown -->
              <div class="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-sm">
                <div class="flex justify-between text-gray-500 dark:text-gray-400">
                  <span>{{ $t('publish.pricing.platformFee', { percent: platformFeePercent }) }}</span>
                  <span>-{{ formatPriceValue(platformFee) }}</span>
                </div>
                <div class="flex justify-between font-medium text-gray-900 dark:text-white mt-1">
                  <span>{{ $t('publish.pricing.youReceive') }}</span>
                  <span class="text-emerald-600">{{ formatPriceValue(sellerAmount) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Private template invite key -->
          <div v-if="form.visibility === 'private'" class="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800">
            <div class="flex items-start gap-3">
              <Key :size="20" class="text-amber-600 mt-0.5" />
              <div class="flex-1">
                <h4 class="font-medium text-amber-800 dark:text-amber-300">{{ $t('publish.inviteKey.title') }}</h4>
                <p class="text-sm text-amber-700 dark:text-amber-400 mt-1">
                  {{ $t('publish.inviteKey.description') }}
                </p>
                <div class="mt-3">
                  <label class="flex items-center gap-2">
                    <input
                      type="checkbox"
                      v-model="form.enableInviteKey"
                      class="w-4 h-4 rounded border-amber-300 text-amber-600 focus:ring-amber-500"
                    />
                    <span class="text-sm text-amber-800 dark:text-amber-300">{{ $t('publish.inviteKey.createOnPublish') }}</span>
                  </label>
                  <div v-if="form.enableInviteKey" class="mt-2">
                    <label class="block text-xs text-amber-700 dark:text-amber-400 mb-1">{{ $t('publish.inviteKey.usageLimit') }}</label>
                    <AppSelect
                      v-model="form.inviteKeyUsageLimit"
                      :options="inviteKeyUsageOptions"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Show in marketplace toggle -->
          <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900 rounded-xl">
            <div>
              <h4 class="font-medium text-gray-900 dark:text-white">{{ $t('publish.showInMarketplace.label') }}</h4>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                {{ form.visibility === 'private' ? $t('publish.showInMarketplace.disabledDesc') : $t('publish.showInMarketplace.enabledDesc') }}
              </p>
            </div>
            <button
              type="button"
              role="switch"
              :aria-checked="form.listed && form.visibility !== 'private'"
              :aria-label="t('accessibility.showInMarketplace')"
              @click="form.listed = !form.listed"
              :disabled="form.visibility === 'private'"
              :class="[
                'relative w-12 h-6 rounded-full transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500',
                form.listed && form.visibility !== 'private'
                  ? 'bg-purple-600'
                  : 'bg-gray-300 dark:bg-gray-600',
                form.visibility === 'private' ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
              ]"
            >
              <span
                aria-hidden="true"
                :class="[
                  'absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform',
                  form.listed && form.visibility !== 'private' ? 'translate-x-6' : 'translate-x-0'
                ]"
              ></span>
            </button>
          </div>

          <!-- Error Message -->
          <div
            v-if="errorMessage"
            class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-600 dark:text-red-400"
          >
            {{ errorMessage }}
          </div>
        </form>

        <!-- Footer -->
        <div class="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
          <button
            type="button"
            @click="close"
            class="px-5 py-2.5 min-h-[44px] text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 font-medium rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-500"
          >
            {{ $t('common.cancel') }}
          </button>
          <button
            @click="submit"
            :disabled="isSubmitting"
            class="px-6 py-2.5 min-h-[44px] bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium rounded-lg transition-all hover:shadow-lg hover:shadow-purple-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-400"
          >
            <Loader2 v-if="isSubmitting" :size="18" class="animate-spin" aria-hidden="true" />
            <Rocket v-else :size="18" aria-hidden="true" />
            <span>{{ isSubmitting ? $t('publish.publishing') : $t('publish.title') }}</span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { X, Globe, Lock, Shield, GitFork, Gift, DollarSign, Key, Loader2, Rocket } from 'lucide-vue-next'
import AppSelect from '@/components/common/AppSelect.vue'
import { templatesAPI } from '@/api/templates'
import { useConfigStore } from '@/stores/configStore'
import { getPlatformFeeRate, previewFeeBreakdown } from '@/constants/marketplace/platformConfig'
import { formatCurrency } from '@/utils/format'

const { t } = useI18n()
const configStore = useConfigStore()

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  template: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'published'])

// Options with i18n (using string literals instead of enum constants)
const visibilityOptions = computed(() => [
  {
    value: 'public',
    label: t('publish.visibility.public'),
    description: t('publish.visibility.publicDesc')
  },
  {
    value: 'private',
    label: t('publish.visibility.private'),
    description: t('publish.visibility.privateDesc')
  }
])

const mutabilityOptions = computed(() => [
  {
    value: 'locked',
    label: t('publish.protection.locked'),
    description: t('publish.protection.lockedDesc')
  },
  {
    value: 'fork_on_use',
    label: t('publish.protection.forkable'),
    description: t('publish.protection.forkableDesc')
  }
])

const pricingOptions = computed(() => [
  {
    value: 'free',
    label: t('publish.pricing.free'),
    description: t('publish.pricing.freeDesc')
  },
  {
    value: 'paid',
    label: t('publish.pricing.paid'),
    description: t('publish.pricing.paidDesc')
  }
])

// Currencies from config store
const currencies = computed(() => {
  const storeCurrencies = configStore.currencies
  if (storeCurrencies.length > 0) {
    return storeCurrencies.map(c => ({ value: c.code, label: `${c.code} (${c.symbol})`, symbol: c.symbol }))
  }
  // Fallback
  return [
    { value: 'USD', label: 'USD ($)', symbol: '$' },
    { value: 'TWD', label: 'TWD (NT$)', symbol: 'NT$' }
  ]
})

const inviteKeyUsageOptions = computed(() => [
  { value: null, label: t('inviteKeys.unlimited') },
  { value: 1, label: t('inviteKeys.uses', { count: 1 }) },
  { value: 5, label: t('inviteKeys.uses', { count: 5 }) },
  { value: 10, label: t('inviteKeys.uses', { count: 10 }) },
  { value: 50, label: t('inviteKeys.uses', { count: 50 }) },
  { value: 100, label: t('inviteKeys.uses', { count: 100 }) }
])

// Form state
const form = reactive({
  visibility: 'public',
  listed: true,
  mutability: 'locked',
  pricing: 'free',
  price: 0,
  currency: 'USD',
  enableInviteKey: true,
  inviteKeyUsageLimit: null
})

const isSubmitting = ref(false)
const errorMessage = ref('')
const platformFeeRate = ref(null)

// Load platform fee rate on mount (REQUIRED)
onMounted(async () => {
  try {
    platformFeeRate.value = await getPlatformFeeRate()
  } catch (e) {
    // Error handled silently
    errorMessage.value = `Platform config error: ${e.message}. Please contact admin.`
  }
})

// Price display (backend now returns dollars directly)
const priceDisplay = computed({
  get: () => form.price,
  set: (val) => { form.price = val || 0 }
})

// Preview-only hints — authoritative fees are computed server-side at purchase time
const feePreview = computed(() => previewFeeBreakdown(form.price, platformFeeRate.value))
const platformFeePercent = computed(() => feePreview.value.feePercent)
const platformFee = computed(() => feePreview.value.platformFee)
const sellerAmount = computed(() => feePreview.value.sellerAmount)

// Format price for display
function formatPriceValue(amount) {
  return formatCurrency(amount, form.currency)
}

// Watch visibility to auto-toggle listed
watch(() => form.visibility, (val) => {
  if (val === 'private') {
    form.listed = false
  }
})

// Reset form when modal opens
watch(() => props.modelValue, (isOpen) => {
  if (isOpen) {
    resetForm()
  }
})

function resetForm() {
  form.visibility = 'public'
  form.listed = true
  form.mutability = 'locked'
  form.pricing = 'free'
  form.price = 0
  form.currency = 'USD'
  form.enableInviteKey = true
  form.inviteKeyUsageLimit = null
  errorMessage.value = ''
}

function close() {
  emit('update:modelValue', false)
}

async function submit() {
  if (isSubmitting.value || !props.template) return

  // Validate
  if (form.pricing === 'paid' && form.price <= 0) {
    errorMessage.value = t('publish.errors.invalidPrice')
    return
  }

  isSubmitting.value = true
  errorMessage.value = ''

  try {
    const templateId = props.template.templateId || props.template.id

    const payload = {
      visibility: form.visibility,
      listed: form.visibility === 'private' ? false : form.listed,
      mutability: form.mutability,
      pricing: form.pricing,
      price: form.pricing === 'paid' ? form.price : 0,
      currency: form.currency,
      enableInviteKey: form.visibility === 'private' && form.enableInviteKey,
      inviteKeyUsageLimit: form.inviteKeyUsageLimit
    }

    // Update template with publish settings
    const updateData = {
      templateStatus: 'published',
      visibility: payload.visibility,
      listed: payload.listed,
      mutability: payload.mutability,
      pricing: payload.pricing,
      price: payload.price,
      currency: payload.currency
    }

    const result = await templatesAPI.updateTemplate(templateId, updateData)

    if (!result.ok) {
      throw new Error(result.error || t('publish.errors.publishFailed'))
    }

    // Create invite key if enabled
    let inviteKey = null
    if (payload.enableInviteKey) {
      const keyResult = await templatesAPI.createInviteKey(templateId, {
        maxUses: payload.inviteKeyUsageLimit || 999
      })
      if (keyResult.ok && keyResult.key) {
        inviteKey = keyResult.key
      }
    }

    close()
    emit('published', {
      templateId,
      inviteKey
    })
  } catch (err) {
    errorMessage.value = err.message || t('publish.errors.publishFailed')
  } finally {
    isSubmitting.value = false
  }
}
</script>

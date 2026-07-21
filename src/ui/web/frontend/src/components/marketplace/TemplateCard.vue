<template>
  <article
    role="button"
    tabindex="0"
    :aria-label="`${template.name} ${$t('common.by')} ${template.creatorName || $t('marketplace.anonymous')}. ${template.pricing === 'free' ? $t('marketplace.free') : formatCurrency(template.price, template.currency)}`"
    class="group relative bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl overflow-hidden cursor-pointer transition-all hover:shadow-xl hover:shadow-purple-500/10 hover:-translate-y-1 hover:border-purple-300 dark:hover:border-purple-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
    @click="$emit('click')"
    @keydown.enter="$emit('click')"
    @keydown.space.prevent="$emit('click')"
  >
    <!-- Hover glow -->
    <div class="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>

    <div class="relative p-5">
      <!-- Header -->
      <div class="flex items-start gap-4 mb-4">
        <!-- Template icon -->
        <TemplateIcon
          :icon-url="customIconUrl"
          :category="template.categorySlug || 'other'"
          size="md"
          :alt="template.name"
        />

        <div class="flex-1 min-w-0">
          <h3 class="font-bold text-gray-900 dark:text-gray-100 truncate group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">
            {{ template.name }}
          </h3>
          <p class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1 mt-0.5">
            <User :size="12" aria-hidden="true" />
            {{ template.creatorName || $t('marketplace.anonymous') }}
          </p>
        </div>

        <!-- Badges -->
        <div class="flex flex-col gap-1">
          <span
            v-if="template.isVerified"
            class="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs font-medium rounded-full flex items-center gap-1"
          >
            <BadgeCheck :size="12" aria-hidden="true" /> {{ $t('marketplace.verified') }}
          </span>
          <span
            v-if="template.isFeatured"
            class="px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 text-xs font-medium rounded-full flex items-center gap-1"
          >
            <Sparkles :size="12" aria-hidden="true" /> {{ $t('marketplace.featured') }}
          </span>
        </div>
      </div>

      <!-- Description -->
      <p class="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2 min-h-[2.5rem]">
        {{ template.description || $t('marketplace.noDescription') }}
      </p>

      <!-- Stats -->
      <div class="flex items-center gap-4 py-3 border-t border-gray-100 dark:border-gray-700">
        <div class="flex items-center gap-1.5 text-gray-500 dark:text-gray-400">
          <Download :size="14" aria-hidden="true" />
          <span class="text-sm font-medium"><span class="sr-only">Downloads:</span>{{ formatCompactNumber(template.downloads) }}</span>
        </div>
        <div v-if="template.rating" class="flex items-center gap-1.5 text-amber-500">
          <Star :size="14" fill="currentColor" aria-hidden="true" />
          <span class="text-sm font-medium"><span class="sr-only">Rating:</span>{{ formatRating(template.rating) }}</span>
        </div>
        <div v-else class="flex items-center gap-1.5 text-gray-300 dark:text-gray-600">
          <Star :size="14" aria-hidden="true" />
          <span class="text-sm font-medium">--</span>
        </div>
        <span
          :class="pricingBadgeClass"
          class="px-2.5 py-1 rounded-full text-xs font-bold ml-auto"
        >
          {{ pricingBadgeText }}
        </span>
      </div>

      <!-- Action Button -->
      <MarketplaceActionButton
        :template="template"
        :is-own-template="isOwnTemplate"
        :is-paid-without-access="isPaidWithoutAccess"
        :is-per-call="isPerCall"
        variant="card"
        @update="$emit('update')"
        @remove="$emit('remove')"
        @purchase="$emit('purchase')"
        @execute-per-call="$emit('execute-per-call')"
        @install="$emit('install')"
      />
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Download, Star, User, BadgeCheck, Sparkles
} from 'lucide-vue-next'
import { formatCurrency, formatCompactNumber, formatRating } from '@/utils/format'
import TemplateIcon from '@/components/common/TemplateIcon.vue'
import MarketplaceActionButton from '@/components/marketplace/MarketplaceActionButton.vue'

const { t } = useI18n()

const props = defineProps({
  template: {
    type: Object,
    required: true
  }
})

defineEmits(['click', 'install', 'remove', 'purchase', 'update', 'execute-per-call'])

// Action flags computed by backend
const isOwnTemplate = computed(() => props.template.isOwnTemplate ?? false)
const isPerCall = computed(() => props.template.isPerCall ?? false)
const isPaidWithoutAccess = computed(() => props.template.isPaidWithoutAccess ?? false)

// Pricing badge styling
const pricingBadgeClass = computed(() => {
  if (props.template.pricing === 'free') {
    return 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
  }
  if (props.template.pricing === 'per_call') {
    return 'bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-400'
  }
  return 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
})

const pricingBadgeText = computed(() => {
  if (props.template.pricing === 'free') {
    return t('marketplace.free')
  }
  if (props.template.pricing === 'per_call') {
    return `${props.template.callPrice} credits/run`
  }
  return formatPrice(props.template.price)
})

// Custom icon URL
const customIconUrl = computed(() => {
  return props.template.iconUrl || props.template.templateIcon || ''
})

function formatPrice(cents) {
  if (!cents) return formatCurrency(0)
  return formatCurrency(cents)
}
</script>

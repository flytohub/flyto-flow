<template>
  <div
    role="button"
    tabindex="0"
    :aria-label="`${template.name} ${$t('common.by')} ${template.creatorName || $t('marketplace.anonymous')}. ${template.pricing === 'free' ? $t('marketplace.free') : formatCurrency(template.price, template.currency)}`"
    class="group bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-4 cursor-pointer transition-all hover:shadow-lg hover:border-purple-300 dark:hover:border-purple-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
    @click="$emit('click')"
    @keydown.enter="$emit('click')"
    @keydown.space.prevent="$emit('click')"
  >
    <div class="flex items-center gap-4">
      <!-- Icon -->
      <div
        class="w-12 h-12 rounded-xl flex items-center justify-center text-white flex-shrink-0 shadow-md"
        :style="{ background: iconGradient }"
      >
        <component :is="categoryIcon" :size="24" :stroke-width="1.5" aria-hidden="true" />
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <h3 class="font-semibold text-gray-900 dark:text-gray-100 truncate group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">
            {{ template.name }}
          </h3>
          <span
            v-if="template.isVerified"
            class="flex-shrink-0"
            :aria-label="$t('marketplace.verified')"
          >
            <BadgeCheck :size="16" class="text-blue-500" aria-hidden="true" />
          </span>
          <span
            v-if="template.isFeatured"
            class="flex-shrink-0"
            :aria-label="$t('marketplace.featured')"
          >
            <Sparkles :size="16" class="text-amber-500" aria-hidden="true" />
          </span>
        </div>

        <p class="text-sm text-gray-500 dark:text-gray-400 truncate mb-2">
          {{ template.description || $t('marketplace.noDescription') }}
        </p>

        <div class="flex items-center gap-4 text-sm">
          <span class="text-gray-400 flex items-center gap-1">
            <User :size="12" aria-hidden="true" />
            {{ template.creatorName || $t('marketplace.anonymous') }}
          </span>
          <span class="text-gray-400 flex items-center gap-1">
            <Download :size="12" aria-hidden="true" />
            <span class="sr-only">{{ $t('marketplace.downloads') }}:</span>{{ formatCompactNumber(template.downloads) }}
          </span>
          <span v-if="template.rating" class="text-amber-500 flex items-center gap-1">
            <Star :size="12" fill="currentColor" aria-hidden="true" />
            <span class="sr-only">{{ $t('marketplace.rating') }}:</span>{{ formatRating(template.rating) }}
          </span>
          <span v-else class="text-gray-300 dark:text-gray-600 flex items-center gap-1">
            <Star :size="12" aria-hidden="true" />
            <span>--</span>
          </span>
          <span
            :class="pricingBadgeClass"
            class="px-2 py-0.5 rounded-full text-xs font-medium"
          >
            {{ pricingBadgeText }}
          </span>
        </div>
      </div>

      <!-- Actions -->
      <MarketplaceActionButton
        :template="template"
        :is-own-template="isOwnTemplate"
        :is-paid-without-access="isPaidWithoutAccess"
        :is-per-call="isPerCall"
        variant="list"
        @update="$emit('update')"
        @remove="$emit('remove')"
        @purchase="$emit('purchase')"
        @execute-per-call="$emit('execute-per-call')"
        @install="$emit('install')"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Download, Star, User, BadgeCheck, Sparkles,
  Zap, Globe, Database, Bell, Brain, Terminal, ShoppingCart, Share2, Cable, Folder
} from 'lucide-vue-next'
import { formatCurrency, formatCompactNumber, formatRating } from '@/utils/format'
import { getCategoryGradient } from '@/constants/colors'
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
  return 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400'
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

const categoryIcons = {
  automation: Zap,
  browser: Globe,
  data: Database,
  notification: Bell,
  ai: Brain,
  devops: Terminal,
  ecommerce: ShoppingCart,
  social: Share2,
  connector: Cable
}

const categoryIcon = computed(() => {
  const slug = props.template.categorySlug || 'other'
  return categoryIcons[slug] || Folder
})

const iconGradient = computed(() => {
  const slug = props.template.categorySlug || 'other'
  return getCategoryGradient(slug)
})

// Format price from cents to dollars
function formatPrice(cents) {
  if (!cents) return formatCurrency(0)
  return formatCurrency(cents)
}
</script>

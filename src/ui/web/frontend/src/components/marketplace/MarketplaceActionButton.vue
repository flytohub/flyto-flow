<template>
  <div @click.stop :class="wrapperClass">
    <!-- Own template: Update listing -->
    <button
      v-if="isOwnTemplate"
      :class="[sharedClass, updateClass]"
      @click="$emit('update')"
    >
      <RefreshCw :size="16" aria-hidden="true" />
      {{ $t('marketplace.updateListing') }}
    </button>
    <!-- Already installed: Remove -->
    <button
      v-else-if="template.isInstalled"
      :class="[sharedClass, removeClass]"
      @click="$emit('remove')"
    >
      <Trash2 :size="16" aria-hidden="true" />
      {{ $t('marketplace.remove') }}
    </button>
    <!-- Paid template without access: Purchase -->
    <button
      v-else-if="isPaidWithoutAccess"
      :class="[sharedClass, purchaseClass]"
      @click="$emit('purchase')"
    >
      <ShoppingCart :size="16" aria-hidden="true" />
      {{ $t('marketplace.purchase') }}
    </button>
    <!-- Per-call template: Execute with credits -->
    <button
      v-else-if="isPerCall"
      :class="[sharedClass, perCallClass]"
      @click="$emit('execute-per-call')"
    >
      <Zap :size="16" aria-hidden="true" />
      {{ $t('marketplace.executePerCall') || 'Run' }} · {{ template.callPrice }} credits
    </button>
    <!-- Free or has access: Install -->
    <button
      v-else
      :class="[sharedClass, installClass]"
      @click="$emit('install')"
    >
      <Plus :size="16" aria-hidden="true" />
      {{ $t('marketplace.install') }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Plus, Trash2, ShoppingCart, RefreshCw, Zap } from 'lucide-vue-next'

const props = defineProps({
  template: {
    type: Object,
    required: true
  },
  isOwnTemplate: {
    type: Boolean,
    default: false
  },
  isPaidWithoutAccess: {
    type: Boolean,
    default: false
  },
  isPerCall: {
    type: Boolean,
    default: false
  },
  variant: {
    type: String,
    default: 'card',
    validator: (v) => ['card', 'list'].includes(v)
  }
})

defineEmits(['update', 'remove', 'purchase', 'execute-per-call', 'install'])

const isCard = computed(() => props.variant === 'card')

const wrapperClass = computed(() =>
  isCard.value ? 'mt-3' : 'flex-shrink-0 hidden sm:block'
)

const sharedClass = computed(() =>
  isCard.value
    ? 'w-full py-2.5 min-h-[44px] font-semibold rounded-xl transition-all flex items-center justify-center gap-2'
    : 'px-4 py-2.5 min-h-[44px] font-medium rounded-lg transition-all flex items-center gap-2'
)

const updateClass = computed(() =>
  isCard.value
    ? 'bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/40 text-purple-600 dark:text-purple-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500 border border-purple-200 dark:border-purple-800'
    : 'bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/40 text-purple-600 dark:text-purple-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500 border border-purple-200 dark:border-purple-800'
)

const removeClass = computed(() =>
  isCard.value
    ? 'bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/40 text-red-600 dark:text-red-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-500 border border-red-200 dark:border-red-800'
    : 'bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/40 text-red-600 dark:text-red-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-500 border border-red-200 dark:border-red-800'
)

const purchaseClass = computed(() =>
  isCard.value
    ? 'bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-white shadow-lg shadow-amber-500/25 hover:shadow-amber-500/40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-400'
    : 'bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-white shadow-md shadow-amber-500/25 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-400'
)

const perCallClass = computed(() =>
  isCard.value
    ? 'bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-400'
    : 'bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white shadow-md shadow-violet-500/25 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-400'
)

const installClass = computed(() =>
  isCard.value
    ? 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-400'
    : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white shadow-md shadow-purple-500/25 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-400'
)
</script>

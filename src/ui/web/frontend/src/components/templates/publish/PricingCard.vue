<template>
  <div :class="[
    'group relative backdrop-blur-xl rounded-2xl p-5 transition-all duration-500',
    pricing === 'per_call'
      ? 'bg-gray-800/50 border border-violet-500/20 hover:border-violet-500/40'
      : 'bg-gray-800/50 border border-white/10 hover:border-emerald-500/30'
  ]">
    <!-- Per-call glow overlay -->
    <div v-if="pricing === 'per_call'" class="absolute inset-0 bg-gradient-to-br from-violet-500/5 via-transparent to-fuchsia-500/5 rounded-2xl pointer-events-none"></div>

    <div class="relative z-10">
      <div class="flex items-center gap-3 mb-4">
        <div :class="[
          'w-8 h-8 rounded-lg flex items-center justify-center',
          pricing === 'per_call'
            ? 'bg-gradient-to-br from-violet-500 to-fuchsia-500'
            : 'bg-gradient-to-br from-emerald-500 to-green-500'
        ]">
          <component :is="pricing === 'per_call' ? Zap : DollarSign" :size="16" class="text-white" />
        </div>
        <h3 class="font-semibold text-white">{{ $t('publish.pricing.label') }}</h3>
      </div>

      <!-- Pricing options -->
      <div class="space-y-2 mb-4">
        <button
          v-for="option in options"
          :key="option.value"
          type="button"
          @click="$emit('update:pricing', option.value)"
          :class="[
            'w-full p-3 rounded-xl text-left transition-all duration-300 border',
            pricing === option.value && option.value === 'per_call'
              ? 'bg-violet-500/20 border-violet-500/50 shadow-lg shadow-violet-500/10'
              : pricing === option.value
                ? 'bg-emerald-500/20 border-emerald-500/50 shadow-lg shadow-emerald-500/10'
                : 'bg-gray-900/30 border-white/5 hover:border-white/20'
          ]"
        >
          <div class="flex items-center gap-2 mb-1">
            <component
              :is="option.value === 'free' ? Gift : option.value === 'per_call' ? Zap : DollarSign"
              :size="14"
              :class="[
                pricing === option.value && option.value === 'per_call' ? 'text-violet-400'
                  : pricing === option.value ? 'text-emerald-400'
                  : 'text-gray-500'
              ]"
            />
            <span :class="[
              pricing === option.value && option.value === 'per_call' ? 'text-violet-300 font-medium'
                : pricing === option.value ? 'text-emerald-300 font-medium'
                : 'text-gray-300'
            ]">
              {{ option.label }}
            </span>
          </div>
          <p class="text-xs text-gray-500 pl-6">{{ option.description }}</p>
        </button>
      </div>

      <!-- Price input (if paid) -->
      <div v-if="pricing === 'paid'" class="space-y-3 pt-3 border-t border-white/10">
        <div class="flex gap-2">
          <div class="flex-1">
            <div class="relative">
              <span class="absolute left-3 top-1/2 -translate-y-1/2 text-emerald-400 font-medium">$</span>
              <input
                :value="priceDisplay"
                @input="$emit('update:price', parseFloat($event.target.value) || 0)"
                type="number"
                min="0"
                step="0.01"
                placeholder="9.99"
                class="w-full pl-8 pr-3 py-2.5 bg-gray-900/50 border border-white/10 rounded-lg text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
              />
            </div>
          </div>
          <AppSelect
            :modelValue="currency"
            @update:modelValue="$emit('update:currency', $event)"
            :options="currencies.map(c => ({ value: c.value, label: c.value }))"
            size="sm"
          />
        </div>
        <div class="p-3 bg-gray-900/50 rounded-lg border border-white/5">
          <div class="flex justify-between text-xs text-gray-400 mb-1">
            <span>{{ $t('publish.pricing.platformFee', { percent: platformFeePercent }) }}</span>
            <span>-{{ formatPrice(platformFee) }}</span>
          </div>
          <div class="flex justify-between text-sm font-medium">
            <span class="text-gray-300">{{ $t('publish.pricing.youReceive') }}</span>
            <span class="text-emerald-400">{{ formatPrice(sellerAmount) }}</span>
          </div>
        </div>
      </div>

      <!-- Per-call pricing panel -->
      <div v-if="pricing === 'per_call'" class="pt-4 border-t border-violet-500/10">
        <!-- Quick presets -->
        <label class="text-xs font-medium text-violet-300/60 uppercase tracking-wider mb-3 block">
          {{ $t('publish.pricing.creditsPerCall') || 'Credits per execution' }}
        </label>
        <div class="grid grid-cols-4 gap-2 mb-4">
          <button
            v-for="preset in presets"
            :key="preset.credits"
            type="button"
            @click="$emit('update:callPrice', preset.credits)"
            :class="[
              'relative py-2.5 rounded-xl text-center transition-all duration-300 border overflow-hidden',
              callPrice === preset.credits
                ? 'bg-violet-500/20 border-violet-500/50 shadow-lg shadow-violet-500/15 scale-[1.02]'
                : 'bg-gray-900/40 border-white/5 hover:border-violet-500/30 hover:bg-violet-500/5'
            ]"
          >
            <!-- Selected glow -->
            <div
              v-if="callPrice === preset.credits"
              class="absolute inset-0 bg-gradient-to-t from-violet-500/10 to-transparent"
            ></div>
            <div class="relative">
              <span :class="[
                'block text-base font-bold tabular-nums',
                callPrice === preset.credits ? 'text-violet-300' : 'text-gray-300'
              ]">{{ preset.credits }}</span>
              <span :class="[
                'block text-[10px] mt-0.5',
                callPrice === preset.credits ? 'text-violet-400/60' : 'text-gray-600'
              ]">${{ preset.usd }}</span>
            </div>
          </button>
        </div>

        <!-- Custom input -->
        <div class="relative group/input">
          <div class="absolute inset-0 rounded-xl bg-gradient-to-r from-violet-500/20 via-fuchsia-500/20 to-violet-500/20 opacity-0 group-focus-within/input:opacity-100 transition-opacity duration-300 blur-xl"></div>
          <div class="relative">
            <Zap :size="14" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-violet-400" />
            <input
              :value="callPrice"
              @input="$emit('update:callPrice', parseInt($event.target.value) || 0)"
              type="number"
              min="1"
              max="100000"
              step="1"
              placeholder="Custom amount"
              class="w-full pl-10 pr-24 py-3 bg-gray-900/60 border border-white/10 rounded-xl text-white text-lg font-semibold tabular-nums focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500/30 transition-all placeholder:text-gray-600 placeholder:font-normal placeholder:text-sm"
            />
            <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 text-xs font-medium">credits / run</span>
          </div>
        </div>

        <!-- Revenue breakdown card -->
        <Transition name="slide-fade">
          <div v-if="callPrice > 0" class="mt-4 relative overflow-hidden rounded-xl">
            <!-- Animated background -->
            <div class="absolute inset-0 bg-gradient-to-br from-violet-900/40 via-gray-900/80 to-fuchsia-900/30"></div>
            <div class="pricing-shimmer"></div>

            <div class="relative p-4 space-y-3">
              <!-- Header -->
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <div class="w-6 h-6 rounded-lg bg-violet-500/20 flex items-center justify-center">
                    <TrendingUp :size="13" class="text-violet-400" />
                  </div>
                  <span class="text-xs font-semibold text-violet-300/80 uppercase tracking-wider">Revenue per call</span>
                </div>
                <span class="text-xs text-gray-500 tabular-nums">≈ {{ callPriceDisplay }}</span>
              </div>

              <!-- Breakdown bars -->
              <div class="space-y-2">
                <!-- Gross -->
                <div class="flex items-center gap-3">
                  <div class="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div class="h-full bg-gradient-to-r from-violet-500 to-fuchsia-500 rounded-full" style="width: 100%"></div>
                  </div>
                  <span class="text-xs text-gray-400 w-20 text-right tabular-nums">{{ callPrice }} cr</span>
                </div>
                <!-- Platform fee -->
                <div class="flex items-center gap-3">
                  <div class="flex-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div class="h-full bg-red-500/50 rounded-full" :style="{ width: platformFeePercent + '%' }"></div>
                  </div>
                  <span class="text-xs text-red-400/70 w-20 text-right tabular-nums">−{{ callPrice - netCredits }} cr</span>
                </div>
              </div>

              <!-- Net result -->
              <div class="flex items-center justify-between pt-3 border-t border-white/5">
                <span class="text-sm text-gray-400">{{ $t('publish.pricing.youReceive') }}</span>
                <div class="flex items-baseline gap-2">
                  <span class="text-2xl font-bold tabular-nums pricing-net-glow">
                    {{ netCredits }}
                  </span>
                  <span class="text-xs text-gray-500">credits</span>
                </div>
              </div>
              <div class="text-right">
                <span class="text-xs text-gray-600 tabular-nums">= {{ netCreditsDisplay }} USD / execution</span>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { DollarSign, Gift, Zap, TrendingUp } from 'lucide-vue-next'
import AppSelect from '@/components/common/AppSelect.vue'
import { formatCurrency, formatCreditsAsUSD } from '@/utils/format'
import { previewNetCredits } from '@/constants/marketplace/platformConfig'

const props = defineProps({
  pricing: { type: String, default: 'free' },
  price: { type: Number, default: 0 },
  callPrice: { type: Number, default: 0 },
  currency: { type: String, default: 'USD' },
  options: { type: Array, required: true },
  currencies: { type: Array, required: true },
  platformFeePercent: { type: Number, default: 15 },
  platformFee: { type: Number, default: 0 },
  sellerAmount: { type: Number, default: 0 }
})

defineEmits(['update:pricing', 'update:price', 'update:callPrice', 'update:currency'])

const priceDisplay = computed(() => props.price)
// Preview-only hints — authoritative fees are computed server-side at purchase time
const netCredits = computed(() => previewNetCredits(props.callPrice, props.platformFeePercent))
const callPriceDisplay = computed(() => formatCreditsAsUSD(props.callPrice))
const netCreditsDisplay = computed(() => formatCreditsAsUSD(netCredits.value))

const presets = [
  { credits: 5, usd: '0.05' },
  { credits: 10, usd: '0.10' },
  { credits: 25, usd: '0.25' },
  { credits: 50, usd: '0.50' },
]

function formatPrice(amount) {
  return formatCurrency(amount, props.currency)
}
</script>

<style scoped>
/* Shimmer scan line on revenue card */
.pricing-shimmer {
  position: absolute;
  top: 0;
  left: -100%;
  width: 50%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.04), transparent);
  animation: pricing-shimmer-move 4s ease-in-out infinite;
  pointer-events: none;
}
@keyframes pricing-shimmer-move {
  0% { left: -50%; }
  100% { left: 150%; }
}

/* Net amount glow */
.pricing-net-glow {
  color: #A78BFA;
  text-shadow: 0 0 20px rgba(167, 139, 250, 0.3);
}

/* Slide-fade transition */
.slide-fade-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-fade-leave-active {
  transition: all 0.2s ease;
}
.slide-fade-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>

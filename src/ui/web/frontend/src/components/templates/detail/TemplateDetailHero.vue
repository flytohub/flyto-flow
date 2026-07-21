<template>
  <div class="relative border-b border-white/10">
    <div class="max-w-7xl mx-auto px-4 py-12">
      <div class="flex flex-col lg:flex-row lg:items-start gap-8">
        <!-- Icon -->
        <TemplateIcon
          :icon-url="iconUrl"
          :category="category"
          size="xl"
          :alt="name"
        />

        <!-- Info -->
        <div class="flex-1 min-w-0">
          <div class="flex flex-wrap items-center gap-3 mb-3">
            <span
              v-if="isVerified"
              class="px-3 py-1 bg-blue-500/20 text-blue-400 text-sm font-medium rounded-full border border-blue-500/30 flex items-center gap-1"
            >
              <BadgeCheck :size="14" /> {{ $t('templateDetail.verified') }}
            </span>
            <span
              v-if="isFeatured"
              class="px-3 py-1 bg-amber-500/20 text-amber-400 text-sm font-medium rounded-full border border-amber-500/30 flex items-center gap-1"
            >
              <Sparkles :size="14" /> {{ $t('templateDetail.featured') }}
            </span>
            <span
              :class="pricing === 'free'
                ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                : 'bg-purple-500/20 text-purple-400 border-purple-500/30'"
              class="px-3 py-1 rounded-full text-sm font-bold border"
            >
              {{ pricing === 'free' ? $t('templateDetail.free') : formattedPrice }}
            </span>
          </div>

          <h1 class="text-3xl lg:text-4xl font-bold text-white mb-3">
            {{ name }}
          </h1>

          <p class="text-gray-400 text-lg mb-6 max-w-2xl">
            {{ description || $t('templateDetail.noDescription') }}
          </p>

          <!-- Stats Row -->
          <div class="flex flex-wrap items-center gap-6">
            <!-- Rating -->
            <div class="flex items-center gap-2">
              <div class="flex items-center">
                <Star
                  v-for="i in 5"
                  :key="i"
                  :size="18"
                  :class="hasRating && i <= Math.round(avgRating) ? 'text-amber-400' : 'text-gray-600'"
                  :fill="hasRating && i <= Math.round(avgRating) ? 'currentColor' : 'none'"
                />
              </div>
              <span v-if="hasRating" class="font-medium text-white">{{ avgRating.toFixed(1) }}</span>
              <span v-else class="text-gray-500 text-sm">{{ $t('templateDetail.noRatings') }}</span>
              <span class="text-gray-500 text-sm">({{ reviewCount }})</span>
            </div>

            <!-- Downloads -->
            <div class="flex items-center gap-2 text-gray-400">
              <Download :size="16" />
              <span>{{ formatCompactNumber(downloads) }} {{ $t('templateDetail.installs') }}</span>
            </div>

            <!-- Author -->
            <router-link
              v-if="creatorId"
              :to="`/creators/${creatorId}`"
              class="flex items-center gap-2 text-gray-400 hover:text-purple-400 transition-colors"
            >
              <img
                v-if="creatorAvatar"
                :src="creatorAvatar"
                :alt="creatorName"
                class="w-6 h-6 rounded-full object-cover"
              />
              <div
                v-else
                class="w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-xs font-bold"
              >
                {{ (creatorName || 'A').charAt(0).toUpperCase() }}
              </div>
              <span>{{ creatorName || $t('templateDetail.anonymous') }}</span>
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { BadgeCheck, Sparkles, Star, Download } from 'lucide-vue-next'
import TemplateIcon from '@/components/common/TemplateIcon.vue'
import { formatCompactNumber } from '@/utils/format'

defineProps({
  category: { type: String, default: 'other' },
  name: { type: String, default: '' },
  description: { type: String, default: '' },
  iconUrl: { type: String, default: '' },
  iconGradient: { type: String, default: '' },
  categoryIcon: { type: [Object, Function], default: null },
  isVerified: { type: Boolean, default: false },
  isFeatured: { type: Boolean, default: false },
  pricing: { type: String, default: 'free' },
  formattedPrice: { type: String, default: '' },
  avgRating: { type: Number, default: 0 },
  reviewCount: { type: Number, default: 0 },
  hasRating: { type: Boolean, default: false },
  downloads: { type: Number, default: 0 },
  creatorId: { type: String, default: '' },
  creatorName: { type: String, default: '' },
  creatorAvatar: { type: String, default: '' }
})

</script>

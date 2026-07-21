<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
    <div class="flex items-start gap-4">
      <!-- Avatar -->
      <div
        class="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0"
      >
        <img
          v-if="review.userAvatar"
          :src="review.userAvatar"
          :alt="review.userName"
          class="w-full h-full rounded-full object-cover"
        />
        <span v-else>{{ (review.userName || 'A').charAt(0).toUpperCase() }}</span>
      </div>

      <div class="flex-1 min-w-0">
        <!-- Header -->
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <span class="font-medium text-gray-900 dark:text-white">{{ review.userName }}</span>
            <span
              v-if="review.isVerifiedPurchase"
              class="px-2 py-0.5 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 text-xs font-medium rounded-full flex items-center gap-1"
            >
              <BadgeCheck :size="12" />
              {{ $t('templateDetail.reviews.verified') }}
            </span>
          </div>
          <span class="text-sm text-gray-500 dark:text-gray-400">{{ formatDate(review.createdAt) }}</span>
        </div>

        <!-- Rating -->
        <div class="flex items-center gap-1 mb-3">
          <Star
            v-for="i in 5"
            :key="i"
            :size="16"
            :class="i <= review.rating ? 'text-amber-400' : 'text-gray-300 dark:text-gray-600'"
            :fill="i <= review.rating ? 'currentColor' : 'none'"
          />
        </div>

        <!-- Comment -->
        <p class="text-gray-600 dark:text-gray-400 whitespace-pre-wrap">{{ review.comment }}</p>

        <!-- Actions -->
        <div v-if="isOwner" class="flex items-center gap-4 mt-4">
          <template v-if="isOwner">
            <button
              @click="$emit('edit', review)"
              class="text-sm text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
            >
              {{ $t('common.edit') }}
            </button>
            <button
              @click="$emit('delete', review.id)"
              class="text-sm text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
            >
              {{ $t('common.delete') }}
            </button>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Star, BadgeCheck } from 'lucide-vue-next'
import { authAPI } from '@/api/auth'
import { formatDate } from '@/utils/format'

const props = defineProps({
  review: {
    type: Object,
    required: true
  }
})

defineEmits(['edit', 'delete'])

const currentUser = authAPI.getLocalUser()
const isOwner = computed(() => currentUser?.id === props.review.userId)

</script>

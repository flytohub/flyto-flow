<template>
  <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
      {{ isEdit ? $t('templateDetail.reviews.update') : $t('templateDetail.reviews.writeReview') }}
    </h3>

    <form @submit.prevent="handleSubmit">
      <!-- Rating -->
      <fieldset class="mb-4">
        <legend class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {{ $t('templateDetail.reviews.yourRating') }}
        </legend>
        <div class="flex gap-1" role="radiogroup" :aria-label="t('accessibility.rating')">
          <button
            v-for="i in 5"
            :key="i"
            type="button"
            role="radio"
            :aria-checked="rating === i"
            :aria-label="`${i} star${i > 1 ? 's' : ''}`"
            @click="rating = i"
            @mouseenter="hoverRating = i"
            @mouseleave="hoverRating = 0"
            class="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center transition-transform hover:scale-110 rounded-lg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
          >
            <Star
              :size="28"
              :class="i <= (hoverRating || rating) ? 'text-amber-400' : 'text-gray-300 dark:text-gray-600'"
              :fill="i <= (hoverRating || rating) ? 'currentColor' : 'none'"
              aria-hidden="true"
            />
          </button>
        </div>
      </fieldset>

      <!-- Comment -->
      <div class="mb-4">
        <label for="review-comment" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {{ $t('templateDetail.reviews.yourReview') }}
        </label>
        <AppTextarea
          id="review-comment"
          v-model="comment"
          :rows="4"
          :placeholder="$t('templateDetail.reviews.reviewPlaceholder')"
          required
        />
      </div>

      <!-- Actions -->
      <div class="flex justify-end gap-3">
        <button
          v-if="isEdit"
          type="button"
          @click="$emit('cancel')"
          class="px-4 py-2.5 min-h-[44px] text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-500"
        >
          {{ $t('templateDetail.reviews.cancel') }}
        </button>
        <button
          type="submit"
          :disabled="submitting || rating === 0 || !comment.trim()"
          class="px-6 py-2.5 min-h-[44px] bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-400"
        >
          <Loader2 v-if="submitting" :size="16" class="animate-spin" aria-hidden="true" />
          {{ submitting ? '' : (isEdit ? $t('templateDetail.reviews.update') : $t('templateDetail.reviews.submit')) }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Star, Loader2 } from 'lucide-vue-next'
import AppTextarea from '@/components/common/AppTextarea.vue'

const { t } = useI18n()

const props = defineProps({
  existingReview: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['submit', 'cancel'])

const rating = ref(0)
const comment = ref('')
const hoverRating = ref(0)
const submitting = ref(false)

const isEdit = computed(() => !!props.existingReview)

onMounted(() => {
  if (props.existingReview) {
    rating.value = props.existingReview.rating
    comment.value = props.existingReview.comment
  }
})

async function handleSubmit() {
  if (rating.value === 0 || !comment.value.trim()) return

  submitting.value = true

  emit('submit', {
    rating: rating.value,
    comment: comment.value.trim()
  })

  // Reset after a short delay (parent will handle actual submission)
  setTimeout(() => {
    submitting.value = false
  }, 500)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @click.self="close"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm"></div>

        <!-- Dialog -->
        <div class="relative w-full max-w-md bg-gray-800 border border-white/10 rounded-2xl shadow-2xl">
          <!-- Header -->
          <div class="flex items-center justify-between p-6 border-b border-white/10">
            <h3 class="text-lg font-semibold text-white flex items-center gap-2">
              <Flag :size="20" class="text-red-400" />
              {{ $t('report.title') }}
            </h3>
            <button
              @click="close"
              class="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
              aria-label="Close"
            >
              <X :size="20" />
            </button>
          </div>

          <!-- Content -->
          <div class="p-6 space-y-4">
            <p class="text-gray-400 text-sm">{{ $t('report.selectReason') }}</p>

            <!-- Reason Options -->
            <div class="space-y-2">
              <label
                v-for="option in reasonOptions"
                :key="option.value"
                class="flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all"
                :class="selectedReason === option.value
                  ? 'bg-red-500/20 border-red-500/50 text-white'
                  : 'bg-gray-900/50 border-white/10 text-gray-300 hover:border-white/20'"
              >
                <input
                  type="radio"
                  :value="option.value"
                  v-model="selectedReason"
                  class="sr-only"
                />
                <div
                  class="w-4 h-4 rounded-full border-2 flex items-center justify-center flex-shrink-0"
                  :class="selectedReason === option.value ? 'border-red-400' : 'border-gray-500'"
                >
                  <div
                    v-if="selectedReason === option.value"
                    class="w-2 h-2 rounded-full bg-red-400"
                  ></div>
                </div>
                <span class="text-sm">{{ option.label }}</span>
              </label>
            </div>

            <!-- Other - Custom Input -->
            <div v-if="selectedReason === 'other'" class="mt-4">
              <AppTextarea
                v-model="customReason"
                :placeholder="$t('report.otherPlaceholder')"
                :rows="3"
              />
            </div>
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-end gap-3 p-6 border-t border-white/10">
            <button
              @click="close"
              class="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors"
            >
              {{ $t('common.cancel') }}
            </button>
            <button
              @click="submit"
              :disabled="!canSubmit || submitting"
              class="px-5 py-2 text-sm font-medium bg-red-500 hover:bg-red-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-xl transition-colors flex items-center gap-2"
            >
              <Loader2 v-if="submitting" :size="16" class="animate-spin" />
              {{ $t('report.submit') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Flag, X, Loader2 } from 'lucide-vue-next'
import AppTextarea from '@/components/common/AppTextarea.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  targetType: { type: String, required: true },
  targetId: { type: String, required: true }
})

const emit = defineEmits(['update:modelValue', 'submit'])

const { t } = useI18n()

const selectedReason = ref('')
const customReason = ref('')
const submitting = ref(false)

const reasonOptions = computed(() => [
  { value: 'inappropriate', label: t('report.reasons.inappropriate') },
  { value: 'spam', label: t('report.reasons.spam') },
  { value: 'misleading', label: t('report.reasons.misleading') },
  { value: 'copyright', label: t('report.reasons.copyright') },
  { value: 'harmful', label: t('report.reasons.harmful') },
  { value: 'other', label: t('report.reasons.other') }
])

const canSubmit = computed(() => {
  if (!selectedReason.value) return false
  if (selectedReason.value === 'other' && !customReason.value.trim()) return false
  return true
})

function close() {
  emit('update:modelValue', false)
  // Reset state
  selectedReason.value = ''
  customReason.value = ''
}

async function submit() {
  if (!canSubmit.value) return

  const reason = selectedReason.value === 'other'
    ? customReason.value.trim()
    : reasonOptions.value.find(o => o.value === selectedReason.value)?.label || selectedReason.value

  submitting.value = true

  emit('submit', {
    targetType: props.targetType,
    targetId: props.targetId,
    reason,
    reasonCode: selectedReason.value
  })
}

// Called by parent after API call completes
function reset() {
  submitting.value = false
  selectedReason.value = ''
  customReason.value = ''
}

defineExpose({ reset })
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: all 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .relative,
.modal-leave-to .relative {
  transform: scale(0.95);
}
</style>

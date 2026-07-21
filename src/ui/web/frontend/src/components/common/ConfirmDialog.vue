<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="show"
        role="alertdialog"
        aria-modal="true"
        :aria-labelledby="title ? 'confirm-dialog-title' : undefined"
        :aria-describedby="message ? 'confirm-dialog-desc' : undefined"
        @click="handleOverlayClick"
        @keydown.esc="$emit('cancel')"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-[1200]"
      >
        <div
          ref="dialogRef"
          tabindex="-1"
          @click.stop
          class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 max-w-md w-full mx-4"
        >
          <!-- Warning Icon for Danger Variant -->
          <div v-if="variant === 'danger'" class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center flex-shrink-0">
              <AlertTriangle :size="20" class="text-red-600 dark:text-red-400" aria-hidden="true" />
            </div>
            <h3 id="confirm-dialog-title" class="text-lg font-bold text-gray-900 dark:text-gray-100">
              {{ computedTitle }}
            </h3>
          </div>
          <h3 v-else id="confirm-dialog-title" class="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">
            {{ computedTitle }}
          </h3>
          <p v-if="computedMessage" id="confirm-dialog-desc" class="text-gray-600 dark:text-gray-400 mb-2">
            {{ computedMessage }}
          </p>
          <!-- Optional body slot for custom content (e.g., input fields) -->
          <div v-if="$slots.body" class="mt-3 mb-2">
            <slot name="body" />
          </div>
          <!-- Destructive Warning -->
          <p v-if="variant === 'danger'" class="text-sm text-red-600 dark:text-red-400 mb-6 flex items-center gap-1">
            <AlertTriangle :size="14" aria-hidden="true" />
            {{ warningText || $t('common.actionCannotBeUndone') }}
          </p>
          <div v-else class="mb-6"></div>
          <div class="flex gap-3 justify-end">
            <button
              v-if="showCancel"
              ref="cancelBtnRef"
              @click="$emit('cancel')"
              class="px-4 py-2.5 min-h-[44px] text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-500"
            >
              {{ computedCancelText }}
            </button>
            <button
              v-if="showSecondary"
              @click="$emit('secondary')"
              class="px-4 py-2.5 min-h-[44px] text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-500"
            >
              {{ secondaryText }}
            </button>
            <button
              ref="confirmBtnRef"
              @click="$emit('confirm')"
              :disabled="loading"
              :class="[confirmClass, loading ? 'opacity-70 cursor-not-allowed' : '']"
              class="px-4 py-2.5 min-h-[44px] text-sm font-medium rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 flex items-center gap-2"
            >
              <Loader2 v-if="loading" :size="16" class="animate-spin" />
              {{ computedConfirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { AlertTriangle, Loader2 } from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps({
  show: { type: Boolean, default: false },
  title: { type: String, default: '' },
  message: { type: String, default: '' },
  confirmText: { type: String, default: '' },
  cancelText: { type: String, default: '' },
  secondaryText: { type: String, default: '' },
  warningText: { type: String, default: '' },
  showCancel: { type: Boolean, default: true },
  showSecondary: { type: Boolean, default: false },
  variant: { type: String, default: 'primary' }, // primary, danger, warning
  closeOnOverlay: { type: Boolean, default: true },
  loading: { type: Boolean, default: false }
})

// Computed i18n defaults
const computedTitle = computed(() => props.title || t('common.confirm'))
const computedMessage = computed(() => props.message || t('confirmDialog.areYouSure'))
const computedConfirmText = computed(() => props.confirmText || t('common.confirm'))
const computedCancelText = computed(() => props.cancelText || t('common.cancel'))

const emit = defineEmits(['confirm', 'cancel', 'secondary'])

const dialogRef = ref(null)
const confirmBtnRef = ref(null)
const cancelBtnRef = ref(null)

const confirmClass = computed(() => {
  switch (props.variant) {
    case 'danger':
      return 'text-white bg-red-600 hover:bg-red-700 focus-visible:outline-red-600'
    case 'warning':
      return 'text-white bg-amber-600 hover:bg-amber-700 focus-visible:outline-amber-600'
    default:
      return 'text-white bg-primary-600 hover:bg-primary-700 focus-visible:outline-primary-600'
  }
})

// Focus management - for danger variant, focus Cancel button to prevent accidental confirmation
watch(() => props.show, async (newVal) => {
  if (newVal) {
    await nextTick()
    if (props.variant === 'danger' && props.showCancel && cancelBtnRef.value) {
      // Focus cancel button for danger variant to prevent accidental destructive action
      cancelBtnRef.value.focus()
    } else if (confirmBtnRef.value) {
      confirmBtnRef.value.focus()
    } else if (dialogRef.value) {
      dialogRef.value.focus()
    }
  }
})

function handleOverlayClick() {
  if (props.closeOnOverlay) {
    emit('cancel')
  }
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

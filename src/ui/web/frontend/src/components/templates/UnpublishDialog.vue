<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-all duration-300"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-all duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
        @click.self="$emit('close')"
      >
        <Transition
          enter-active-class="transition-all duration-300"
          enter-from-class="scale-95 opacity-0"
          enter-to-class="scale-100 opacity-100"
          leave-active-class="transition-all duration-200"
          leave-from-class="scale-100 opacity-100"
          leave-to-class="scale-95 opacity-0"
        >
          <div
            v-if="show"
            class="w-full max-w-md bg-gray-800 rounded-2xl border border-white/10 shadow-2xl overflow-hidden"
          >
            <!-- Header -->
            <div class="p-6 border-b border-white/10">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-xl bg-red-500/20 flex items-center justify-center">
                  <AlertTriangle :size="24" class="text-red-400" />
                </div>
                <div>
                  <h3 class="text-lg font-semibold text-white">{{ $t('publishPage.unpublishConfirmTitle') }}</h3>
                  <p class="text-sm text-gray-400">{{ templateName }}</p>
                </div>
              </div>
            </div>

            <!-- Body -->
            <div class="p-6">
              <p class="text-gray-300 mb-4">{{ $t('publishPage.unpublishConfirmMessage') }}</p>
              <ul class="space-y-2 text-sm text-gray-400">
                <li class="flex items-start gap-2">
                  <span class="text-red-400 mt-0.5">•</span>
                  {{ $t('publishPage.unpublishWarning1') }}
                </li>
                <li class="flex items-start gap-2">
                  <span class="text-red-400 mt-0.5">•</span>
                  {{ $t('publishPage.unpublishWarning2') }}
                </li>
                <li class="flex items-start gap-2">
                  <span class="text-amber-400 mt-0.5">•</span>
                  {{ $t('publishPage.unpublishWarning3') }}
                </li>
              </ul>
            </div>

            <!-- Footer -->
            <div class="p-6 bg-gray-900/50 border-t border-white/10 flex justify-end gap-3">
              <button
                @click="$emit('close')"
                :disabled="loading"
                aria-label="Cancel"
                class="px-5 py-2.5 text-gray-300 hover:text-white hover:bg-white/10 rounded-xl transition-all"
              >
                {{ $t('common.cancel') }}
              </button>
              <button
                @click="$emit('confirm')"
                :disabled="loading"
                class="px-5 py-2.5 bg-red-600 hover:bg-red-700 text-white font-medium rounded-xl transition-all flex items-center gap-2 disabled:opacity-50"
              >
                <Loader2 v-if="loading" :size="18" class="animate-spin" />
                <EyeOff v-else :size="18" />
                {{ loading ? $t('publishPage.unpublishing') : $t('publishPage.confirmUnpublish') }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { AlertTriangle, EyeOff, Loader2 } from 'lucide-vue-next'

defineProps({
  show: { type: Boolean, default: false },
  templateName: { type: String, default: '' },
  loading: { type: Boolean, default: false }
})

defineEmits(['close', 'confirm'])
</script>

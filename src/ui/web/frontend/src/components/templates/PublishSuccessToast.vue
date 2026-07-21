<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="translate-y-4 opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-4 opacity-0"
    >
      <div
        v-if="message || inviteKey"
        class="fixed bottom-6 right-6 z-50 max-w-md"
      >
        <!-- Simple success (no invite key) -->
        <div
          v-if="!inviteKey"
          class="px-5 py-3 bg-emerald-600 text-white rounded-xl shadow-lg flex items-center gap-3"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <span class="font-medium">{{ message }}</span>
        </div>

        <!-- Success with invite key -->
        <div v-else class="relative overflow-hidden">
          <div class="absolute -inset-0.5 bg-gradient-to-r from-amber-500 to-orange-500 rounded-2xl blur opacity-50"></div>
          <div class="relative bg-gray-900 rounded-2xl border border-amber-500/30 p-5">
            <div class="flex items-center gap-3 mb-3">
              <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <p class="font-semibold text-white">{{ $t('publish.publishSuccess') }}</p>
                <p class="text-sm text-gray-400">{{ $t('inviteKeys.copyHint') }}</p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <code class="flex-1 px-4 py-2.5 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-300 font-mono tracking-widest text-center">
                {{ inviteKey }}
              </code>
              <button
                @click="$emit('copy')"
                class="p-2.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-400 rounded-xl transition-colors"
                :title="$t('common.copy')"
              >
                <Copy v-if="!copied" :size="18" />
                <Check v-else :size="18" class="text-emerald-400" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { Copy, Check } from 'lucide-vue-next'

defineProps({
  message: { type: String, default: '' },
  inviteKey: { type: String, default: '' },
  copied: { type: Boolean, default: false }
})

defineEmits(['copy'])
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
        @click.self="$emit('cancel')"
      >
        <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-md shadow-xl">
          <!-- Header -->
          <div class="p-6 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                {{ $t('wallet.confirmExecute') }}
              </h3>
              <button
                @click="$emit('cancel')"
                class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <X :size="20" />
              </button>
            </div>
          </div>

          <!-- Content -->
          <div class="p-6 space-y-4">
            <!-- Template Info -->
            <div class="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 space-y-3">
              <div class="flex justify-between text-sm">
                <span class="text-gray-500 dark:text-gray-400">Template</span>
                <span class="font-medium text-gray-900 dark:text-white truncate ml-4">{{ templateName }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-500 dark:text-gray-400">{{ $t('wallet.executionCost') }}</span>
                <span class="font-semibold text-violet-600 dark:text-violet-400">{{ callPrice }} credits</span>
              </div>
              <div class="border-t border-gray-200 dark:border-gray-600 pt-3 flex justify-between text-sm">
                <span class="text-gray-500 dark:text-gray-400">{{ $t('wallet.yourBalance') }}</span>
                <span :class="[
                  'font-semibold',
                  hasEnough ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'
                ]">
                  {{ balance }} credits
                </span>
              </div>
            </div>

            <!-- Insufficient Balance Warning -->
            <div v-if="!hasEnough" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-xl p-4">
              <div class="flex gap-3">
                <AlertCircle :size="20" class="text-red-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p class="font-medium text-red-800 dark:text-red-300 text-sm">
                    {{ $t('wallet.insufficientCredits') }}
                  </p>
                  <p class="text-red-700 dark:text-red-400 text-xs mt-1">
                    {{ $t('wallet.needMore', { amount: callPrice - balance }) || `You need ${callPrice - balance} more credits` }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
            <button
              @click="$emit('cancel')"
              class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              {{ $t('common.cancel') }}
            </button>
            <router-link
              v-if="!hasEnough"
              to="/wallet"
              class="px-5 py-2 text-sm font-medium text-white bg-violet-600 rounded-lg hover:bg-violet-700 transition-colors flex items-center gap-2"
            >
              <Plus :size="16" />
              {{ $t('wallet.topupNow') }}
            </router-link>
            <button
              v-else
              @click="$emit('confirm')"
              :disabled="loading"
              class="px-5 py-2 text-sm font-medium text-white bg-violet-600 rounded-lg hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <Loader2 v-if="loading" :size="16" class="animate-spin" />
              <Zap v-else :size="16" />
              {{ $t('wallet.confirmAndExecute') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { X, AlertCircle, Plus, Zap, Loader2 } from 'lucide-vue-next'

const props = defineProps({
  templateName: { type: String, required: true },
  callPrice: { type: Number, required: true },
  balance: { type: Number, required: true },
  loading: { type: Boolean, default: false },
})

defineEmits(['confirm', 'cancel'])

const hasEnough = computed(() => props.balance >= props.callPrice)
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

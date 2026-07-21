<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
        @click.self="$emit('close')"
      >
        <div class="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-lg shadow-xl">
          <!-- Header -->
          <div class="p-6 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center justify-between">
              <h3 class="text-xl font-semibold text-gray-900 dark:text-white">
                {{ $t('wallet.topupTitle') }}
              </h3>
              <button
                @click="$emit('close')"
                class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <X :size="20" />
              </button>
            </div>
          </div>

          <!-- Loading -->
          <div v-if="loading" class="p-12 flex justify-center">
            <Loader2 :size="24" class="animate-spin text-gray-400" />
          </div>

          <!-- Packages Grid -->
          <div v-else class="p-6">
            <div class="grid grid-cols-2 gap-3">
              <button
                v-for="pkg in walletStore.packages"
                :key="pkg.credits"
                @click="selectedPackage = pkg"
                :class="[
                  'relative border-2 rounded-xl p-4 text-left transition-all',
                  selectedPackage?.credits === pkg.credits
                    ? 'border-violet-500 bg-violet-50 dark:bg-violet-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                ]"
              >
                <div class="text-2xl font-bold text-gray-900 dark:text-white">
                  {{ pkg.credits.toLocaleString() }}
                </div>
                <div class="text-sm text-gray-500 dark:text-gray-400">credits</div>
                <div class="mt-2 text-lg font-semibold text-violet-600 dark:text-violet-400">
                  ${{ pkg.priceDisplay.toFixed(2) }}
                </div>
                <!-- Selected indicator -->
                <div
                  v-if="selectedPackage?.credits === pkg.credits"
                  class="absolute top-2 right-2 w-5 h-5 bg-violet-500 rounded-full flex items-center justify-center"
                >
                  <Check :size="14" class="text-white" />
                </div>
              </button>
            </div>

            <p class="text-xs text-gray-400 dark:text-gray-500 mt-4 text-center">
              {{ $t('wallet.conversionNote') }}
            </p>
          </div>

          <!-- Footer -->
          <div class="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
            <button
              @click="$emit('close')"
              class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              {{ $t('common.cancel') }}
            </button>
            <button
              @click="handleTopup"
              :disabled="!selectedPackage || processing"
              class="px-6 py-2 text-sm font-medium text-white bg-violet-600 rounded-lg hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <Loader2 v-if="processing" :size="16" class="animate-spin" />
              <CreditCard v-else :size="16" />
              {{ $t('wallet.proceedToPayment') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { X, Loader2, Check, CreditCard } from 'lucide-vue-next'
import { useWalletStore } from '@/stores/walletStore'

defineEmits(['close'])

const walletStore = useWalletStore()
const loading = ref(true)
const selectedPackage = ref(null)
const processing = ref(false)

async function handleTopup() {
  if (!selectedPackage.value) return
  processing.value = true
  try {
    await walletStore.topup(selectedPackage.value.credits)
  } catch (err) {
    // Error handled by store
  } finally {
    processing.value = false
  }
}

onMounted(async () => {
  await walletStore.fetchPackages()
  loading.value = false
  // Auto-select first package
  if (walletStore.packages.length > 0) {
    selectedPackage.value = walletStore.packages[0]
  }
})
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

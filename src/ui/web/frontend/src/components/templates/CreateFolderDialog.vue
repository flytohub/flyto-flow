<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
        @click.self="$emit('cancel')"
      >
        <div class="w-full max-w-md animate-scale-in">
          <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl shadow-2xl p-6">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              {{ $t('templateFolders.newFolder') }}
            </h3>

            <!-- Folder Name Input -->
            <div class="mb-5">
              <input
                ref="nameInput"
                v-model="name"
                type="text"
                :placeholder="$t('templateFolders.folderName')"
                class="w-full px-4 py-2.5 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                @keydown.enter="handleConfirm"
              />
            </div>

            <!-- Color Picker -->
            <div class="mb-6">
              <label class="block text-sm text-gray-500 dark:text-gray-400 mb-2">
                {{ $t('templateFolders.selectColor') }}
              </label>
              <div class="flex items-center gap-3">
                <button
                  v-for="c in colors"
                  :key="c.value"
                  class="color-dot"
                  :class="{ 'is-selected': selectedColor === c.value }"
                  :style="{ '--dot-color': c.value }"
                  :title="c.label"
                  @click="selectedColor = c.value"
                >
                  <Check v-if="selectedColor === c.value" :size="12" class="text-white" />
                </button>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex justify-end gap-3">
              <button
                @click="$emit('cancel')"
                class="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
              >
                {{ $t('common.cancel') }}
              </button>
              <button
                @click="handleConfirm"
                :disabled="!name.trim() || loading"
                class="px-5 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 rounded-lg transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <Loader2 v-if="loading" :size="14" class="animate-spin" />
                {{ $t('common.create') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { Check, Loader2 } from 'lucide-vue-next'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['confirm', 'cancel'])

const nameInput = ref(null)
const name = ref('')
const selectedColor = ref('#8B5CF6')

const colors = [
  { value: '#8B5CF6', label: 'Purple' },
  { value: '#3B82F6', label: 'Blue' },
  { value: '#10B981', label: 'Green' },
  { value: '#F59E0B', label: 'Amber' },
  { value: '#EF4444', label: 'Red' },
  { value: '#EC4899', label: 'Pink' },
  { value: '#06B6D4', label: 'Cyan' },
  { value: '#6B7280', label: 'Gray' },
]

watch(() => props.show, async (v) => {
  if (v) {
    name.value = ''
    selectedColor.value = '#8B5CF6'
    await nextTick()
    nameInput.value?.focus()
  }
})

function handleConfirm() {
  if (props.loading) return
  if (!name.value.trim()) return
  emit('confirm', { name: name.value.trim(), color: selectedColor.value })
}
</script>

<style scoped>
.color-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--dot-color);
  border: 2px solid transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

.color-dot:hover {
  transform: scale(1.15);
  box-shadow: 0 0 12px color-mix(in srgb, var(--dot-color) 50%, transparent);
}

.color-dot.is-selected {
  border-color: white;
  transform: scale(1.15);
  box-shadow: 0 0 16px color-mix(in srgb, var(--dot-color) 60%, transparent);
}

.fade-enter-active { transition: opacity 0.2s ease; }
.fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.animate-scale-in {
  animation: scale-in 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes scale-in {
  from { opacity: 0; transform: scale(0.92) translateY(8px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
</style>

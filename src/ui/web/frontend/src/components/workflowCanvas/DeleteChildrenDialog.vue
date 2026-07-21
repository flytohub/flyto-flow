<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="show"
        @click="$emit('cancel')"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      >
        <div
          @click.stop
          class="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl p-6 max-w-md w-full mx-4"
        >
          <h3 class="text-lg font-bold text-slate-100 mb-2">
            {{ $t('workflowCanvas.deleteDialog.title') }}
          </h3>
          <p class="text-slate-400 mb-6">
            {{ $t('workflowCanvas.deleteDialog.message', { count: childCount }) }}
          </p>
          <div class="flex flex-col gap-2">
            <button
              @click="$emit('merge')"
              class="w-full px-4 py-3 text-sm font-medium text-left rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400 hover:bg-purple-500/20 transition-colors"
            >
              <div class="font-semibold">{{ $t('workflowCanvas.deleteDialog.mergeToChild') }}</div>
              <div class="text-xs text-purple-400/70 mt-0.5">{{ $t('workflowCanvas.deleteDialog.mergeToChildDesc') }}</div>
            </button>
            <button
              @click="$emit('delete-all')"
              class="w-full px-4 py-3 text-sm font-medium text-left rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 transition-colors"
            >
              <div class="font-semibold">{{ $t('workflowCanvas.deleteDialog.deleteAll') }}</div>
              <div class="text-xs text-red-400/70 mt-0.5">{{ $t('workflowCanvas.deleteDialog.deleteAllDesc', { count: childCount }) }}</div>
            </button>
            <button
              @click="$emit('cancel')"
              class="w-full px-4 py-2 text-sm font-medium text-slate-400 hover:bg-slate-700 rounded-lg transition-colors mt-2"
            >
              {{ $t('common.cancel') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
defineProps({
  show: {
    type: Boolean,
    default: false
  },
  childCount: {
    type: Number,
    default: 0
  }
})

defineEmits(['merge', 'delete-all', 'cancel'])
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

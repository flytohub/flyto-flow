<template>
  <div class="space-y-4">
    <!-- Status Filter -->
    <div class="flex items-center gap-2">
      <button
        v-for="s in statusOptions"
        :key="s.value"
        @click="$emit('filterStatus', s.value)"
        :class="[
          'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
          status === s.value
            ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
            : 'text-gray-400 hover:text-white hover:bg-white/5'
        ]"
      >
        {{ s.label }}
        <span v-if="s.value === 'open' && openCount" class="ml-1 text-xs opacity-70">({{ openCount }})</span>
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="w-8 h-8 border-2 border-purple-500/20 border-t-purple-500 rounded-full animate-spin"></div>
    </div>

    <!-- List -->
    <template v-else>
      <TransitionGroup name="list" tag="div" class="space-y-3">
        <PullRequestCard
          v-for="(pr, i) in pullRequests"
          :key="pr.id"
          :pr="pr"
          :style="{ animationDelay: `${i * 50}ms` }"
          @select="$emit('select', $event)"
        />
      </TransitionGroup>

      <!-- Empty -->
      <div v-if="!pullRequests.length" class="text-center py-12">
        <GitPullRequest :size="32" class="mx-auto mb-2 text-gray-600" />
        <p class="text-gray-400">{{ $t('templateCollaboration.pullRequests.noOpenPRs') }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { GitPullRequest } from 'lucide-vue-next'
import PullRequestCard from './PullRequestCard.vue'

const { t } = useI18n()

defineProps({
  pullRequests: { type: Array, default: () => [] },
  status: { type: String, default: null },
  openCount: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
})

defineEmits(['select', 'filterStatus'])

const statusOptions = computed(() => [
  { value: null, label: t('templateCollaboration.filters.all') },
  { value: 'open', label: t('templateCollaboration.pullRequests.statusOpen') },
  { value: 'merged', label: t('templateCollaboration.pullRequests.statusMerged') },
  { value: 'rejected', label: t('templateCollaboration.pullRequests.statusRejected') },
  { value: 'closed', label: t('templateCollaboration.pullRequests.statusClosed') },
])
</script>

<style scoped>
.list-enter-active {
  animation: list-in 0.3s ease-out both;
}
.list-leave-active {
  animation: list-in 0.2s ease reverse both;
}
.list-move {
  transition: transform 0.3s ease;
}
@keyframes list-in {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>

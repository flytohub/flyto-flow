<template>
  <div
    @click="$emit('select', pr)"
    class="p-4 bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 hover:border-purple-500/30 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-purple-500/10 transition-all duration-200 cursor-pointer group"
  >
    <div class="flex items-start justify-between gap-3">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <PullRequestStatusBadge :status="pr.status" />
          <h3 class="text-white font-medium truncate group-hover:text-purple-400 transition-colors">
            {{ pr.title }}
          </h3>
        </div>
        <p class="text-sm text-gray-500">
          {{ $t('templateCollaboration.pullRequests.openedBy', { name: pr.authorName }) }}
          &middot;
          {{ formatTimeAgo(pr.createdAt) }}
        </p>
      </div>
    </div>

    <!-- Diff Summary -->
    <div v-if="hasDiff" class="mt-3 flex items-center gap-3 text-xs">
      <span v-if="pr.diffSummary?.addedSteps?.length" class="text-emerald-400">
        +{{ pr.diffSummary.addedSteps.length }} {{ $t('templateCollaboration.pullRequests.stepsAdded') }}
      </span>
      <span v-if="pr.diffSummary?.removedSteps?.length" class="text-red-400">
        -{{ pr.diffSummary.removedSteps.length }} {{ $t('templateCollaboration.pullRequests.stepsRemoved') }}
      </span>
      <span v-if="pr.diffSummary?.modifiedSteps?.length" class="text-amber-400">
        ~{{ pr.diffSummary.modifiedSteps.length }} {{ $t('templateCollaboration.pullRequests.stepsModified') }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import PullRequestStatusBadge from './PullRequestStatusBadge.vue'

const props = defineProps({
  pr: { type: Object, required: true }
})

defineEmits(['select'])

const hasDiff = computed(() => {
  const d = props.pr.diffSummary
  if (!d) return false
  return (d.addedSteps?.length || 0) + (d.removedSteps?.length || 0) + (d.modifiedSteps?.length || 0) > 0
})

function formatTimeAgo(dateStr) {
  if (!dateStr) return ''
  const now = new Date()
  const date = new Date(dateStr)
  const diff = Math.floor((now - date) / 1000)
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  if (diff < 2592000) return `${Math.floor(diff / 86400)}d ago`
  return date.toLocaleDateString()
}
</script>

<template>
  <div
    @click="$emit('select', issue)"
    class="p-4 bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 hover:border-emerald-500/30 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-emerald-500/10 transition-all duration-200 cursor-pointer group"
  >
    <div class="flex items-start justify-between gap-3">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <span :class="statusClass" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium">
            <component :is="statusIcon" :size="12" />
            {{ issue.status }}
          </span>
          <span :class="typeClass" class="px-2 py-0.5 rounded-full text-xs font-medium">
            {{ issue.type }}
          </span>
          <h3 class="text-white font-medium truncate group-hover:text-emerald-400 transition-colors">
            {{ issue.title }}
          </h3>
        </div>
        <p class="text-sm text-gray-500">
          {{ issue.authorName }} &middot; {{ formatTimeAgo(issue.createdAt) }}
        </p>
      </div>

      <div class="flex items-center gap-3 text-sm text-gray-500 flex-shrink-0">
        <span v-if="issue.commentCount" class="flex items-center gap-1">
          <MessageSquare :size="14" />
          {{ issue.commentCount }}
        </span>
        <span v-if="issue.upvotes" class="flex items-center gap-1">
          <ThumbsUp :size="14" />
          {{ issue.upvotes }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { CircleDot, CheckCircle2, MessageSquare, ThumbsUp, Bug, Lightbulb, HelpCircle } from 'lucide-vue-next'

const props = defineProps({
  issue: { type: Object, required: true }
})

defineEmits(['select'])

const statusClass = computed(() =>
  props.issue.status === 'open'
    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
    : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
)

const statusIcon = computed(() => props.issue.status === 'open' ? CircleDot : CheckCircle2)

const typeClass = computed(() => ({
  bug: 'bg-red-500/20 text-red-400',
  feature: 'bg-blue-500/20 text-blue-400',
  question: 'bg-amber-500/20 text-amber-400',
}[props.issue.type] || 'bg-gray-500/20 text-gray-400'))

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

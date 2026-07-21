<template>
  <div class="space-y-4">
    <!-- Timeline -->
    <div v-if="activity.length" class="relative">
      <!-- Vertical line -->
      <div class="absolute left-4 top-2 bottom-2 w-px bg-white/10"></div>

      <div
        v-for="(event, i) in activity"
        :key="`${event.type}-${event.created_at}-${i}`"
        class="relative pl-10 pb-6 last:pb-0 animate-slide-in"
        :style="{ animationDelay: `${i * 50}ms` }"
      >
        <!-- Dot -->
        <div :class="[
          'absolute left-2 w-4 h-4 rounded-full border-2 flex items-center justify-center',
          dotClasses(event)
        ]">
          <component :is="eventIcon(event)" :size="10" class="text-current" />
        </div>

        <!-- Card -->
        <div class="bg-gray-800/30 rounded-2xl border border-white/5 p-4 hover:border-white/10 hover:shadow-md transition-all duration-200">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0 flex-1">
              <p class="text-sm text-white">
                {{ eventDescription(event) }}
              </p>
              <p class="text-xs text-gray-500 mt-1">
                <span v-if="event.actor_name" class="text-gray-400">{{ event.actor_name }}</span>
                <span v-if="event.actor_name && event.created_at"> &middot; </span>
                <span v-if="event.created_at">{{ formatDate(event.created_at) }}</span>
              </p>
              <!-- Extra data for certain events -->
              <p
                v-if="event.type === 'commented' && event.data?.body"
                class="text-xs text-gray-400 mt-2 line-clamp-3 whitespace-pre-line"
              >
                {{ event.data.body }}
              </p>
              <p
                v-if="event.type === 'label_added' && event.data?.label"
                class="mt-2"
              >
                <span class="px-1.5 py-0.5 bg-blue-500/15 text-blue-400 rounded text-xs">
                  {{ event.data.label }}
                </span>
              </p>
              <p
                v-if="event.type === 'reviewed' && event.data?.body"
                class="text-xs text-gray-400 mt-2 line-clamp-3 whitespace-pre-line"
              >
                {{ event.data.body }}
              </p>
            </div>

            <!-- Type badge -->
            <span :class="[
              'shrink-0 px-1.5 py-0.5 rounded text-xs flex items-center gap-1',
              badgeClasses(event)
            ]">
              <component :is="eventIcon(event)" :size="10" />
              {{ badgeLabel(event) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty -->
    <div v-else class="text-center py-12">
      <GitPullRequest :size="32" class="mx-auto mb-2 text-gray-600" />
      <p class="text-gray-400">No activity yet</p>
    </div>
  </div>
</template>

<script setup>
import {
  GitPullRequest,
  Check,
  X,
  MessageSquare,
  GitMerge,
  Ban,
  RefreshCw,
  Zap,
  Tag,
} from 'lucide-vue-next'

defineProps({
  activity: { type: Array, default: () => [] },
})

const EVENT_CONFIG = {
  created: { icon: GitPullRequest, color: 'emerald', label: 'Created' },
  'reviewed:approve': { icon: Check, color: 'emerald', label: 'Approved' },
  'reviewed:reject': { icon: X, color: 'red', label: 'Rejected' },
  reviewed: { icon: MessageSquare, color: 'blue', label: 'Reviewed' },
  commented: { icon: MessageSquare, color: 'blue', label: 'Comment' },
  merged: { icon: GitMerge, color: 'purple', label: 'Merged' },
  closed: { icon: Ban, color: 'gray', label: 'Closed' },
  reopened: { icon: RefreshCw, color: 'emerald', label: 'Reopened' },
  ready: { icon: Zap, color: 'amber', label: 'Ready' },
  label_added: { icon: Tag, color: 'blue', label: 'Label' },
}

const COLOR_MAP = {
  emerald: {
    dot: 'bg-emerald-500 border-emerald-400 text-emerald-100',
    badge: 'bg-emerald-500/15 text-emerald-400',
  },
  red: {
    dot: 'bg-red-500 border-red-400 text-red-100',
    badge: 'bg-red-500/15 text-red-400',
  },
  blue: {
    dot: 'bg-blue-500 border-blue-400 text-blue-100',
    badge: 'bg-blue-500/15 text-blue-400',
  },
  purple: {
    dot: 'bg-purple-500 border-purple-400 text-purple-100',
    badge: 'bg-purple-500/15 text-purple-400',
  },
  gray: {
    dot: 'bg-gray-500 border-gray-400 text-gray-100',
    badge: 'bg-gray-500/15 text-gray-400',
  },
  amber: {
    dot: 'bg-amber-500 border-amber-400 text-amber-100',
    badge: 'bg-amber-500/15 text-amber-400',
  },
}

function getConfig(event) {
  if (event.type === 'reviewed' && event.data?.action) {
    const key = `reviewed:${event.data.action}`
    if (EVENT_CONFIG[key]) return EVENT_CONFIG[key]
  }
  return EVENT_CONFIG[event.type] || EVENT_CONFIG.commented
}

function eventIcon(event) {
  return getConfig(event).icon
}

function dotClasses(event) {
  const color = getConfig(event).color
  return COLOR_MAP[color]?.dot || COLOR_MAP.gray.dot
}

function badgeClasses(event) {
  const color = getConfig(event).color
  return COLOR_MAP[color]?.badge || COLOR_MAP.gray.badge
}

function badgeLabel(event) {
  return getConfig(event).label
}

function eventDescription(event) {
  const actor = event.actor_name || 'Someone'
  switch (event.type) {
    case 'created':
      return `${actor} opened this pull request`
    case 'reviewed':
      if (event.data?.action === 'approve')
        return `${actor} approved the changes`
      if (event.data?.action === 'reject')
        return `${actor} requested changes`
      return `${actor} submitted a review`
    case 'commented':
      return `${actor} left a comment`
    case 'merged':
      return `${actor} merged this pull request`
    case 'closed':
      return `${actor} closed this pull request`
    case 'reopened':
      return `${actor} reopened this pull request`
    case 'ready':
      return `${actor} marked this as ready for review`
    case 'label_added':
      return `${actor} added a label`
    default:
      return `${actor} performed an action`
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.animate-slide-in {
  animation: slide-in 0.35s ease-out both;
}
@keyframes slide-in {
  from { opacity: 0; transform: translateX(-12px); }
  to { opacity: 1; transform: translateX(0); }
}
</style>

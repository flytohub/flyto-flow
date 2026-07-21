<template>
  <div
    @click="$emit('click', issue)"
    class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-4 hover:border-purple-500/30 cursor-pointer transition-all group"
  >
    <div class="flex items-start gap-3">
      <!-- Type Icon -->
      <div :class="typeIconContainerClass(issue.type)" class="mt-0.5 flex-shrink-0">
        <component :is="typeIcon(issue.type)" :size="16" class="text-white" />
      </div>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 flex-wrap">
          <h3 class="font-semibold text-white text-sm group-hover:text-purple-300 transition-colors truncate">
            {{ issue.title }}
          </h3>
          <span
            v-for="label in issue.labels"
            :key="label"
            class="px-2 py-0.5 text-xs rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30"
          >
            {{ label }}
          </span>
        </div>
        <div class="flex items-center gap-3 mt-1 text-xs text-gray-500">
          <span>{{ issue.author_name }}</span>
          <span>{{ formatDate(issue.created_at) }}</span>
          <span :class="priorityDotClass(issue.priority)" class="flex items-center gap-1">
            <span class="w-1.5 h-1.5 rounded-full" :class="priorityDotBg(issue.priority)"></span>
            {{ $t(`issues.priority.${issue.priority}`, issue.priority) }}
          </span>
        </div>
      </div>

      <!-- Stats -->
      <div class="flex items-center gap-4 flex-shrink-0 text-xs text-gray-500">
        <span v-if="issue.upvotes > 0" class="flex items-center gap-1 text-purple-400">
          <ThumbsUp :size="14" />
          {{ issue.upvotes }}
        </span>
        <span v-if="issue.comment_count > 0" class="flex items-center gap-1 text-gray-400">
          <MessageSquare :size="14" />
          {{ issue.comment_count }}
        </span>
        <span v-if="issue.images?.length > 0" class="flex items-center gap-1 text-gray-400">
          <ImageIcon :size="14" />
          {{ issue.images.length }}
        </span>
        <span :class="statusDotClass(issue.status)" class="w-2.5 h-2.5 rounded-full"></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import {
  CircleDot, Bug, Lightbulb, HelpCircle,
  ThumbsUp, MessageSquare, Image as ImageIcon
} from 'lucide-vue-next'

const { t } = useI18n()

defineProps({
  issue: { type: Object, required: true },
  formatDate: { type: Function, required: true },
})

defineEmits(['click'])

function typeIcon(type) {
  switch (type) {
    case 'bug': return Bug
    case 'feature': return Lightbulb
    case 'question': return HelpCircle
    default: return CircleDot
  }
}

function typeIconContainerClass(type) {
  switch (type) {
    case 'bug': return 'w-8 h-8 rounded-lg flex items-center justify-center bg-gradient-to-br from-red-500 to-orange-500'
    case 'feature': return 'w-8 h-8 rounded-lg flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-500'
    case 'question': return 'w-8 h-8 rounded-lg flex items-center justify-center bg-gradient-to-br from-blue-500 to-cyan-500'
    default: return 'w-8 h-8 rounded-lg flex items-center justify-center bg-gray-700'
  }
}

function priorityDotClass(priority) {
  switch (priority) {
    case 'high': return 'text-red-400'
    case 'medium': return 'text-yellow-400'
    default: return 'text-gray-500'
  }
}

function priorityDotBg(priority) {
  switch (priority) {
    case 'high': return 'bg-red-400'
    case 'medium': return 'bg-yellow-400'
    default: return 'bg-gray-500'
  }
}

function statusDotClass(status) {
  switch (status) {
    case 'open': return 'bg-green-400 shadow-lg shadow-green-400/30'
    case 'in_progress': return 'bg-yellow-400 shadow-lg shadow-yellow-400/30'
    case 'closed': return 'bg-gray-500'
    default: return 'bg-gray-500'
  }
}
</script>

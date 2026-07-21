<template>
  <div>
    <!-- Back Button -->
    <button
      @click="$emit('close')"
      class="flex items-center gap-1.5 text-sm text-gray-400 hover:text-white mb-6 transition-colors"
    >
      <ArrowLeft :size="16" />
      {{ $t('issues.backToList', 'Back to issues') }}
    </button>

    <!-- Issue Header Card -->
    <div class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6 mb-6">
      <div class="flex items-start justify-between gap-4">
        <div class="flex-1 min-w-0">
          <h1 class="text-2xl font-bold text-white break-words mb-3">
            {{ issue.title }}
          </h1>
          <div class="flex items-center gap-2 flex-wrap">
            <span :class="statusBadgeClass(issue.status)">
              {{ $t(`issues.status.${issue.status}`, issue.status) }}
            </span>
            <span :class="typeBadgeClass(issue.type)">
              <component :is="typeIcon(issue.type)" :size="12" />
              {{ $t(`issues.type.${issue.type}`, issue.type) }}
            </span>
            <span :class="priorityBadgeClass(issue.priority)">
              {{ $t(`issues.priority.${issue.priority}`, issue.priority) }}
            </span>
            <span v-for="label in issue.labels" :key="label"
              class="px-2.5 py-0.5 text-xs rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30"
            >
              {{ label }}
            </span>
          </div>
        </div>

        <!-- Admin Actions -->
        <div v-if="isAdmin" class="flex items-center gap-2 flex-shrink-0">
          <button
            v-if="issue.status !== 'closed'"
            @click="$emit('update-status', issue.id, 'closed')"
            class="px-3 py-1.5 text-sm bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/30 transition-colors"
          >
            {{ $t('issues.close', 'Close') }}
          </button>
          <button
            v-if="issue.status === 'closed'"
            @click="$emit('update-status', issue.id, 'open')"
            class="px-3 py-1.5 text-sm bg-green-500/20 text-green-400 border border-green-500/30 rounded-lg hover:bg-green-500/30 transition-colors"
          >
            {{ $t('issues.reopen', 'Reopen') }}
          </button>
          <button
            @click="$emit('delete', issue.id)"
            class="px-3 py-1.5 text-sm bg-gray-700/50 text-gray-400 border border-white/10 rounded-lg hover:bg-gray-700 hover:text-red-400 transition-colors"
          >
            <Trash2 :size="14" />
          </button>
        </div>
      </div>
    </div>

    <!-- Description Card -->
    <div class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6 mb-6">
      <div class="flex items-center gap-3 mb-4">
        <img
          v-if="issue.author_avatar"
          :src="issue.author_avatar"
          class="w-8 h-8 rounded-full ring-2 ring-purple-500/30"
        />
        <div v-else class="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center ring-2 ring-purple-500/30">
          <User :size="14" class="text-purple-400" />
        </div>
        <span class="font-medium text-white text-sm">{{ issue.author_name }}</span>
        <span class="text-xs text-gray-500">{{ formatDate(issue.created_at) }}</span>
      </div>
      <div class="prose-issue text-gray-300 text-sm leading-relaxed" v-html="renderMarkdown(issue.description)"></div>

      <!-- Issue Images -->
      <div v-if="issue.images?.length" class="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-3">
        <div
          v-for="(img, idx) in issue.images"
          :key="idx"
          @click="$emit('open-lightbox', issue.images, idx)"
          class="relative group cursor-pointer rounded-xl overflow-hidden border border-white/10 hover:border-purple-500/30 transition-colors"
        >
          <img :src="img" class="w-full h-32 object-cover" />
          <div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
            <ZoomIn :size="20" class="text-white opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>
      </div>
    </div>

    <!-- Upvote -->
    <div class="flex items-center gap-4 mb-8">
      <button
        @click="$emit('toggle-upvote', issue.id)"
        :disabled="!isLoggedIn"
        :class="[
          'flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-all border',
          hasUpvoted
            ? 'bg-purple-500/20 text-purple-300 border-purple-500/30 shadow-lg shadow-purple-500/10'
            : 'bg-gray-800/50 text-gray-400 border-white/10 hover:border-purple-500/30 hover:text-purple-300',
          !isLoggedIn && 'opacity-50 cursor-not-allowed'
        ]"
      >
        <ThumbsUp :size="16" />
        {{ issue.upvotes || 0 }}
      </button>
    </div>

    <!-- Comments Section -->
    <div class="border-t border-white/10 pt-6">
      <h3 class="text-lg font-semibold text-white mb-4">
        {{ $t('issues.comments', 'Comments') }} ({{ comments.length }})
      </h3>

      <!-- Comment List -->
      <div class="space-y-4 mb-6">
        <div
          v-for="comment in comments"
          :key="comment.id"
          class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-4"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <img
                v-if="comment.author_avatar"
                :src="comment.author_avatar"
                class="w-6 h-6 rounded-full ring-1 ring-white/20"
              />
              <div v-else class="w-6 h-6 rounded-full bg-gray-700 flex items-center justify-center ring-1 ring-white/20">
                <User :size="12" class="text-gray-400" />
              </div>
              <span class="font-medium text-sm text-white">{{ comment.author_name }}</span>
              <span class="text-xs text-gray-500">{{ formatDate(comment.created_at) }}</span>
            </div>
            <button
              v-if="canDeleteComment(comment)"
              @click="$emit('delete-comment', issue.id, comment.id)"
              class="text-gray-500 hover:text-red-400 transition-colors"
            >
              <Trash2 :size="14" />
            </button>
          </div>
          <div class="prose-issue text-gray-300 text-sm" v-html="renderMarkdown(comment.content)"></div>

          <!-- Comment Images -->
          <div v-if="comment.images?.length" class="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-2">
            <div
              v-for="(img, idx) in comment.images"
              :key="idx"
              @click="$emit('open-lightbox', comment.images, idx)"
              class="relative group cursor-pointer rounded-lg overflow-hidden border border-white/10 hover:border-purple-500/30 transition-colors"
            >
              <img :src="img" class="w-full h-24 object-cover" />
              <div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
                <ZoomIn :size="16" class="text-white opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty Comments -->
      <div v-if="!commentsLoading && comments.length === 0" class="text-center py-8 text-gray-500 text-sm">
        {{ $t('issues.noComments', 'No comments yet. Be the first to comment!') }}
      </div>

      <!-- Add Comment -->
      <slot name="comment-form"></slot>
    </div>
  </div>
</template>

<script setup>
import {
  ArrowLeft, Trash2, User, ThumbsUp, ZoomIn,
  CircleDot, Bug, Lightbulb, HelpCircle
} from 'lucide-vue-next'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

defineProps({
  issue: { type: Object, required: true },
  comments: { type: Array, default: () => [] },
  commentsLoading: { type: Boolean, default: false },
  isAdmin: { type: Boolean, default: false },
  isLoggedIn: { type: Boolean, default: false },
  hasUpvoted: { type: Boolean, default: false },
  currentUser: { type: Object, default: null },
  formatDate: { type: Function, required: true },
  canDeleteComment: { type: Function, default: () => false },
})

defineEmits([
  'close',
  'update-status',
  'delete',
  'toggle-upvote',
  'delete-comment',
  'open-lightbox',
])

function renderMarkdown(content) {
  if (!content) return ''
  const html = marked(content)
  return DOMPurify.sanitize(html)
}



function typeIcon(type) {
  switch (type) {
    case 'bug': return Bug
    case 'feature': return Lightbulb
    case 'question': return HelpCircle
    default: return CircleDot
  }
}

function statusBadgeClass(status) {
  switch (status) {
    case 'open': return 'inline-flex px-2.5 py-0.5 text-xs font-medium rounded-full bg-green-500/20 text-green-300 border border-green-500/30'
    case 'in_progress': return 'inline-flex px-2.5 py-0.5 text-xs font-medium rounded-full bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'
    case 'closed': return 'inline-flex px-2.5 py-0.5 text-xs font-medium rounded-full bg-gray-700 text-gray-400 border border-white/10'
    default: return 'inline-flex px-2.5 py-0.5 text-xs font-medium rounded-full bg-gray-700 text-gray-400 border border-white/10'
  }
}

function typeBadgeClass(type) {
  switch (type) {
    case 'bug': return 'inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-medium rounded-full bg-red-500/20 text-red-300 border border-red-500/30'
    case 'feature': return 'inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-medium rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30'
    case 'question': return 'inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-medium rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30'
    default: return 'inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-medium rounded-full bg-gray-700 text-gray-300 border border-white/10'
  }
}

function priorityBadgeClass(priority) {
  switch (priority) {
    case 'high': return 'inline-flex px-2.5 py-0.5 text-xs font-medium rounded-full bg-red-500/20 text-red-300 border border-red-500/30'
    case 'medium': return 'inline-flex px-2.5 py-0.5 text-xs font-medium rounded-full bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'
    case 'low': return 'inline-flex px-2.5 py-0.5 text-xs font-medium rounded-full bg-gray-700 text-gray-400 border border-white/10'
    default: return 'inline-flex px-2.5 py-0.5 text-xs font-medium rounded-full bg-gray-700 text-gray-400 border border-white/10'
  }
}
</script>

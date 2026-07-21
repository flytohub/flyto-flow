<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Back -->
    <button @click="$emit('back')" aria-label="Back" class="text-sm text-gray-400 hover:text-white flex items-center gap-1 transition-colors">
      <ArrowLeft :size="14" />
      {{ $t('common.back') }}
    </button>

    <!-- Issue Header -->
    <div class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6">
      <div class="flex items-start justify-between mb-4">
        <div class="flex-1">
          <div class="flex items-center gap-2 mb-2">
            <span :class="statusClass" class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium">
              {{ issue.status }}
            </span>
            <span :class="typeClass" class="px-2 py-0.5 rounded-full text-xs font-medium">
              {{ issue.type }}
            </span>
          </div>
          <h2 class="text-xl font-bold text-white">{{ issue.title }}</h2>
          <p class="text-sm text-gray-400 mt-1">
            {{ issue.authorName }} &middot; {{ formatDate(issue.createdAt) }}
          </p>
        </div>

        <div class="flex items-center gap-2">
          <!-- Upvote -->
          <button
            @click="$emit('upvote', issue.id)"
            aria-label="Upvote"
            :class="[
              'flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm transition-all',
              isUpvoted
                ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            ]"
          >
            <ThumbsUp :size="14" />
            {{ issue.upvotes || 0 }}
          </button>

          <!-- Close -->
          <button
            v-if="canClose && issue.status === 'open'"
            @click="$emit('close', issue.id)"
            aria-label="Close issue"
            class="px-3 py-1.5 text-sm text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all"
          >
            {{ $t('templateCollaboration.templateIssues.closeIssue') }}
          </button>

          <!-- Reopen -->
          <button
            v-if="canClose && issue.status === 'closed'"
            @click="$emit('reopen', issue.id)"
            aria-label="Reopen issue"
            class="px-3 py-1.5 text-sm text-emerald-400 hover:bg-emerald-500/10 border border-emerald-500/30 rounded-lg transition-all flex items-center gap-1"
          >
            <RefreshCw :size="12" />
            {{ $t('templateCollaboration.templateIssues.reopen') }}
          </button>
        </div>
      </div>

      <div v-if="issue.description" class="prose prose-invert prose-sm max-w-none" v-html="renderMd(issue.description)"></div>

      <div v-if="issue.labels?.length" class="flex flex-wrap gap-1.5 mt-4">
        <span v-for="label in issue.labels" :key="label" class="px-2 py-0.5 bg-gray-700/50 text-gray-300 rounded-full text-xs">
          {{ label }}
        </span>
      </div>

      <!-- Assignees -->
      <div v-if="issue.assignees?.length" class="flex items-center gap-2 mt-4">
        <span class="text-xs text-gray-500">{{ $t('templateCollaboration.templateIssues.assignees') }}:</span>
        <div class="flex -space-x-1">
          <div
            v-for="a in issue.assignees"
            :key="a.user_id"
            class="w-6 h-6 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center text-white text-xs font-bold border-2 border-gray-800"
            :title="a.user_name"
          >
            {{ (a.user_name || 'A').charAt(0).toUpperCase() }}
          </div>
        </div>
      </div>

      <!-- Linked PRs -->
      <div v-if="issue.linkedPrIds?.length || issue.linked_pr_ids?.length" class="flex items-center gap-2 mt-3 flex-wrap">
        <span class="text-xs text-gray-500">{{ $t('templateCollaboration.pullRequests.linkedPRs') }}:</span>
        <span
          v-for="prId in (issue.linkedPrIds || issue.linked_pr_ids || [])"
          :key="prId"
          class="px-2 py-0.5 bg-purple-500/10 text-purple-400 border border-purple-500/20 rounded-full text-xs"
        >
          PR#{{ prId.slice(0, 8) }}
        </span>
      </div>

      <!-- Reactions -->
      <EmojiReactions
        v-if="issue.reactions && Object.keys(issue.reactions).length"
        :reactions="issue.reactions"
        :current-user-id="currentUserId"
        class="mt-4"
        @toggle="$emit('toggleReaction', { type: $event })"
      />
    </div>

    <!-- Comments -->
    <div class="space-y-4">
      <h3 class="text-sm font-medium text-gray-400">
        {{ $t('templateCollaboration.templateIssues.comments') }} ({{ comments.length }})
      </h3>

      <div v-if="!comments.length" class="text-center py-8">
        <MessageSquare :size="32" class="mx-auto mb-2 text-gray-600" />
        <p class="text-sm text-gray-500">{{ $t('templateCollaboration.pullRequests.startConversation') }}</p>
      </div>

      <TransitionGroup name="comment" tag="div" class="space-y-3">
        <div
          v-for="comment in comments"
          :key="comment.id"
          class="p-4 bg-gray-800/30 rounded-2xl border border-white/5 hover:border-white/10 transition-colors duration-200 group"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <div class="w-6 h-6 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
                {{ (comment.authorName || comment.author_name || 'A').charAt(0).toUpperCase() }}
              </div>
              <span class="text-sm font-medium text-white">{{ comment.authorName || comment.author_name }}</span>
              <span class="text-xs text-gray-500">{{ formatDate(comment.createdAt || comment.created_at) }}</span>
              <span v-if="comment.updatedAt || comment.updated_at" class="text-xs text-gray-600 italic">{{ $t('templateCollaboration.comments.edited') }}</span>
            </div>

            <!-- Edit/Delete menu -->
            <div v-if="canEditComment(comment)" class="opacity-0 group-hover:opacity-100 transition-opacity">
              <div class="relative">
                <button
                  @click="toggleCommentMenu(comment.id)"
                  aria-label="Comment actions"
                  class="p-1 text-gray-500 hover:text-white rounded transition-colors"
                >
                  <MoreHorizontal :size="14" />
                </button>
                <div
                  v-if="openMenuId === comment.id"
                  class="absolute right-0 top-6 z-10 bg-gray-800 border border-white/10 rounded-lg shadow-xl py-1 min-w-28"
                >
                  <button
                    v-if="isCommentAuthor(comment)"
                    @click="startEditComment(comment)"
                    aria-label="Edit comment"
                    class="w-full px-3 py-1.5 text-left text-sm text-gray-300 hover:bg-white/5 flex items-center gap-2"
                  >
                    <Pencil :size="12" /> {{ $t('templateCollaboration.comments.edit') }}
                  </button>
                  <button
                    @click="$emit('deleteComment', comment.id); openMenuId = null"
                    aria-label="Delete comment"
                    class="w-full px-3 py-1.5 text-left text-sm text-red-400 hover:bg-red-500/10 flex items-center gap-2"
                  >
                    <Trash2 :size="12" /> {{ $t('templateCollaboration.comments.delete') }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Edit mode -->
          <div v-if="editingCommentId === comment.id" class="space-y-2">
            <textarea
              v-model="editContent"
              rows="3"
              class="w-full bg-gray-900/50 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm focus:border-purple-500/50 focus:outline-none resize-none"
            ></textarea>
            <div class="flex items-center gap-2">
              <button
                @click="saveEditComment(comment.id)"
                :disabled="!editContent.trim()"
                aria-label="Save edit"
                class="px-3 py-1.5 bg-purple-500/20 text-purple-400 rounded-lg text-xs font-medium transition-all disabled:opacity-50"
              >
                {{ $t('common.save') }}
              </button>
              <button @click="cancelEditComment" aria-label="Cancel edit" class="px-3 py-1.5 text-gray-500 text-xs">{{ $t('common.cancel') }}</button>
            </div>
          </div>
          <div v-else class="prose prose-invert prose-sm max-w-none" v-html="renderMd(comment.content)"></div>

          <!-- Comment Reactions -->
          <EmojiReactions
            v-if="comment.reactions && Object.keys(comment.reactions).length"
            :reactions="comment.reactions"
            :current-user-id="currentUserId"
            class="mt-2"
            @toggle="$emit('toggleCommentReaction', { commentId: comment.id, type: $event })"
          />
        </div>
      </TransitionGroup>

      <!-- Comment Form -->
      <div class="space-y-2">
        <textarea
          v-model="newComment"
          rows="3"
          :placeholder="$t('templateCollaboration.templateIssues.addComment')"
          class="w-full bg-gray-900/50 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-gray-500 focus:border-purple-500/50 focus:outline-none text-sm transition-colors resize-none"
          @keydown.meta.enter="submitComment"
          @keydown.ctrl.enter="submitComment"
        ></textarea>
        <div class="flex items-center justify-between">
          <span class="text-xs text-gray-600">Markdown supported</span>
          <button
            @click="submitComment"
            :disabled="!newComment.trim()"
            class="px-4 py-2 bg-purple-500/20 text-purple-400 hover:bg-purple-500/30 border border-purple-500/30 rounded-xl text-sm font-medium transition-all disabled:opacity-50"
          >
            {{ $t('templateCollaboration.templateIssues.send') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ArrowLeft, ThumbsUp, RefreshCw, MessageSquare, MoreHorizontal, Pencil, Trash2 } from 'lucide-vue-next'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import EmojiReactions from '@/components/common/EmojiReactions.vue'

const props = defineProps({
  issue: { type: Object, required: true },
  comments: { type: Array, default: () => [] },
  canClose: { type: Boolean, default: false },
  isUpvoted: { type: Boolean, default: false },
  isOwner: { type: Boolean, default: false },
  currentUserId: { type: String, default: '' },
})

const emit = defineEmits([
  'back', 'close', 'reopen', 'upvote', 'comment',
  'deleteComment', 'editComment',
  'toggleReaction', 'toggleCommentReaction',
])

const newComment = ref('')
const openMenuId = ref(null)
const editingCommentId = ref(null)
const editContent = ref('')

const statusClass = computed(() =>
  props.issue.status === 'open'
    ? 'bg-emerald-500/20 text-emerald-400'
    : 'bg-gray-500/20 text-gray-400'
)

const typeClass = computed(() => ({
  bug: 'bg-red-500/20 text-red-400',
  feature: 'bg-blue-500/20 text-blue-400',
  question: 'bg-amber-500/20 text-amber-400',
}[props.issue.type] || 'bg-gray-500/20 text-gray-400'))

function canEditComment(comment) {
  const authorId = comment.authorId || comment.author_id
  return props.isOwner || authorId === props.currentUserId
}

function isCommentAuthor(comment) {
  const authorId = comment.authorId || comment.author_id
  return authorId === props.currentUserId
}

function toggleCommentMenu(id) {
  openMenuId.value = openMenuId.value === id ? null : id
}

function startEditComment(comment) {
  editingCommentId.value = comment.id
  editContent.value = comment.content
  openMenuId.value = null
}

function saveEditComment(commentId) {
  if (!editContent.value.trim()) return
  emit('editComment', { commentId, content: editContent.value.trim() })
  editingCommentId.value = null
  editContent.value = ''
}

function cancelEditComment() {
  editingCommentId.value = null
  editContent.value = ''
}

function renderMd(content) {
  if (!content) return ''
  return DOMPurify.sanitize(marked(content))
}

function submitComment() {
  if (!newComment.value.trim()) return
  emit('comment', newComment.value.trim())
  newComment.value = ''
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric'
  })
}
</script>

<style scoped>
.animate-fade-in {
  animation: fade-in 0.3s ease-out;
}
@keyframes fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.comment-enter-active {
  animation: slide-up 0.35s ease-out;
}
.comment-leave-active {
  animation: fade-out 0.2s ease-in forwards;
}
@keyframes slide-up {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes fade-out {
  from { opacity: 1; transform: scale(1); }
  to { opacity: 0; transform: scale(0.95); }
}
.prose :deep(h1) { @apply text-lg font-bold mb-3 text-white; }
.prose :deep(h2) { @apply text-base font-semibold mb-2 text-white; }
.prose :deep(h3) { @apply text-sm font-medium mb-2 text-white; }
.prose :deep(p) { @apply mb-2 text-gray-300; }
.prose :deep(ul) { @apply list-disc pl-5 mb-2 text-gray-300; }
.prose :deep(ol) { @apply list-decimal pl-5 mb-2 text-gray-300; }
.prose :deep(li) { @apply mb-1; }
.prose :deep(code) { @apply bg-purple-500/20 text-purple-300 px-1.5 py-0.5 rounded text-xs; }
.prose :deep(pre) { @apply bg-gray-900 p-3 rounded-lg overflow-x-auto mb-2 border border-white/10; }
.prose :deep(blockquote) { @apply border-l-4 border-purple-500 pl-3 italic text-gray-400; }
.prose :deep(a) { @apply text-purple-400 hover:text-purple-300 underline; }
</style>

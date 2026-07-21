<template>
  <div class="space-y-6 animate-fade-in">
    <!-- Back -->
    <button @click="$emit('back')" aria-label="Back" class="text-sm text-gray-400 hover:text-white flex items-center gap-1 transition-colors">
      <ArrowLeft :size="14" />
      {{ $t('common.back') }}
    </button>

    <!-- Header -->
    <div class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6">
      <div class="flex items-start justify-between mb-4">
        <div class="flex-1">
          <div class="flex items-center gap-2 mb-2 flex-wrap">
            <PullRequestStatusBadge :status="pr.status" :is-draft="pr.isDraft" />
            <span
              v-for="label in (pr.labels || [])"
              :key="label"
              :class="labelClass(label)"
              class="px-2 py-0.5 rounded-full text-xs font-medium"
            >
              {{ label }}
            </span>
          </div>
          <h2 class="text-xl font-bold text-white">{{ pr.title }}</h2>
          <p class="text-sm text-gray-400 mt-1">
            {{ $t('templateCollaboration.pullRequests.openedBy', { name: pr.authorName }) }}
            &middot;
            {{ formatDate(pr.createdAt) }}
          </p>
        </div>
      </div>

      <!-- Description -->
      <div v-if="pr.description" class="prose prose-invert prose-sm max-w-none mt-4" v-html="renderMd(pr.description)"></div>

      <!-- Linked Issues -->
      <div v-if="pr.linkedIssueIds?.length" class="mt-4 flex items-center gap-2 flex-wrap">
        <span class="text-xs text-gray-500">{{ $t('templateCollaboration.pullRequests.linkedIssues') }}:</span>
        <span
          v-for="issueId in pr.linkedIssueIds"
          :key="issueId"
          class="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full text-xs"
        >
          #{{ issueId.slice(0, 8) }}
        </span>
      </div>

      <!-- Reactions -->
      <EmojiReactions
        v-if="pr.reactions && Object.keys(pr.reactions).length"
        :reactions="pr.reactions"
        :current-user-id="currentUserId"
        class="mt-4"
        @toggle="$emit('toggleReaction', { type: $event })"
      />

      <!-- Diff Summary -->
      <div class="mt-6 p-4 bg-gray-900/50 rounded-xl border border-white/5">
        <h3 class="text-sm font-medium text-gray-400 mb-3">{{ $t('templateCollaboration.pullRequests.diffSummary') }}</h3>
        <div class="flex flex-wrap gap-4 text-sm">
          <div class="flex items-center gap-1 text-emerald-400">
            <Plus :size="14" />
            {{ pr.diffSummary?.addedSteps?.length || pr.diffSummary?.added_steps?.length || 0 }} {{ $t('templateCollaboration.pullRequests.stepsAdded') }}
          </div>
          <div class="flex items-center gap-1 text-red-400">
            <Minus :size="14" />
            {{ pr.diffSummary?.removedSteps?.length || pr.diffSummary?.removed_steps?.length || 0 }} {{ $t('templateCollaboration.pullRequests.stepsRemoved') }}
          </div>
          <div class="flex items-center gap-1 text-amber-400">
            <Pencil :size="14" />
            {{ pr.diffSummary?.modifiedSteps?.length || pr.diffSummary?.modified_steps?.length || 0 }} {{ $t('templateCollaboration.pullRequests.stepsModified') }}
          </div>
        </div>
      </div>

      <!-- Diff View -->
      <PullRequestDiffView
        v-if="showDiff"
        :diff-summary="pr.diffSummary || {}"
        :proposed-workflow="pr.proposedWorkflow || pr.proposed_workflow || {}"
        class="mt-4"
      />
      <button
        @click="showDiff = !showDiff"
        aria-label="Toggle diff"
        class="mt-2 text-xs text-purple-400 hover:text-purple-300 transition-colors"
      >
        {{ showDiff ? $t('templateCollaboration.pullRequests.hideDiff') : $t('templateCollaboration.pullRequests.showDiff') }}
      </button>

      <!-- Merge Conflict Warning -->
      <div
        v-if="mergeCheckData?.has_conflict"
        class="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-center gap-2"
      >
        <ShieldAlert :size="16" class="text-amber-400 flex-shrink-0" />
        <p class="text-sm text-amber-300">
          {{ $t('templateCollaboration.pullRequests.conflictWarning') }}
          (v{{ mergeCheckData.base_version }} → v{{ mergeCheckData.current_version }})
        </p>
      </div>
    </div>

    <!-- Reviewers -->
    <div v-if="(pr.reviews || []).length" class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6">
      <h3 class="text-sm font-medium text-gray-400 mb-3">{{ $t('templateCollaboration.pullRequests.reviews') }} ({{ pr.reviews.length }})</h3>
      <div class="space-y-3">
        <div
          v-for="(review, idx) in pr.reviews"
          :key="idx"
          class="flex items-start gap-3 p-3 bg-gray-900/30 rounded-xl border border-white/5"
        >
          <div
            :class="review.action === 'approve' ? 'from-emerald-500 to-teal-500' : 'from-red-500 to-pink-500'"
            class="w-8 h-8 bg-gradient-to-br rounded-full flex items-center justify-center text-white flex-shrink-0"
          >
            <Check v-if="review.action === 'approve'" :size="14" />
            <X v-else :size="14" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-white">{{ review.reviewer_name }}</span>
              <span :class="review.action === 'approve' ? 'text-emerald-400' : 'text-red-400'" class="text-xs font-medium">
                {{ review.action === 'approve' ? $t('templateCollaboration.pullRequests.approved') : $t('templateCollaboration.pullRequests.rejected') }}
              </span>
            </div>
            <div v-if="review.comment" class="text-sm text-gray-400 mt-1">{{ review.comment }}</div>
            <span class="text-xs text-gray-600">{{ formatDate(review.reviewed_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Legacy Review Comment (backward compat) -->
    <div v-else-if="pr.reviewComment" class="mt-4 p-4 bg-blue-500/10 rounded-xl border border-blue-500/20">
      <p class="text-sm text-blue-300 font-medium mb-1">{{ pr.reviewerName }}</p>
      <div class="prose prose-invert prose-sm max-w-none prose-p:text-blue-300" v-html="renderMd(pr.reviewComment)"></div>
    </div>

    <!-- Activity Timeline -->
    <PRActivityTimeline
      v-if="(pr.activity || []).length > 1"
      :activity="pr.activity"
    />

    <!-- Comments Section -->
    <div class="space-y-4">
      <h3 class="text-sm font-medium text-gray-400">
        {{ $t('templateCollaboration.pullRequests.comments') }} ({{ comments.length }})
      </h3>

      <!-- Empty -->
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
          <!-- Display mode -->
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
          :placeholder="$t('templateCollaboration.pullRequests.addComment')"
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

    <!-- Actions -->
    <div class="flex items-center gap-3 flex-wrap">
      <!-- Owner actions for open PRs -->
      <template v-if="isOwner && pr.status === 'open'">
        <!-- Mark Ready (for drafts) -->
        <button
          v-if="pr.isDraft || pr.is_draft"
          @click="$emit('ready', pr.id)"
          aria-label="Mark ready"
          class="px-4 py-2 bg-amber-500/20 text-amber-400 hover:bg-amber-500/30 border border-amber-500/30 rounded-xl transition-all text-sm flex items-center gap-2"
        >
          <Zap :size="14" />
          {{ $t('templateCollaboration.pullRequests.markReady') }}
        </button>

        <!-- Merge (not for drafts) -->
        <button
          v-if="!(pr.isDraft || pr.is_draft)"
          @click="$emit('merge', pr.id)"
          :disabled="mergeCheckData && !mergeCheckData.can_merge"
          aria-label="Merge"
          class="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:shadow-lg hover:shadow-purple-500/30 text-white font-medium rounded-xl transition-all text-sm flex items-center gap-2 disabled:opacity-50"
        >
          <GitMerge :size="14" />
          {{ $t('templateCollaboration.pullRequests.merge') }}
          <span v-if="mergeCheckData?.min_reviewers > 0" class="text-xs opacity-70">
            ({{ mergeCheckData.approvals }}/{{ mergeCheckData.min_reviewers }})
          </span>
        </button>

        <button
          @click="$emit('approve', pr.id)"
          aria-label="Approve"
          class="px-4 py-2 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 border border-emerald-500/30 rounded-xl transition-all text-sm flex items-center gap-2"
        >
          <Check :size="14" />
          {{ $t('templateCollaboration.pullRequests.approve') }}
        </button>
        <button
          @click="$emit('reject', pr.id)"
          aria-label="Reject"
          class="px-4 py-2 bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30 rounded-xl transition-all text-sm flex items-center gap-2"
        >
          <X :size="14" />
          {{ $t('templateCollaboration.pullRequests.reject') }}
        </button>
        <button
          @click="$emit('close', pr.id)"
          aria-label="Close"
          class="px-4 py-2 text-gray-400 hover:text-white hover:bg-white/5 rounded-xl transition-all text-sm"
        >
          {{ $t('templateCollaboration.pullRequests.close') }}
        </button>
      </template>

      <!-- Reopen button for closed/rejected PRs -->
      <button
        v-if="(pr.status === 'closed' || pr.status === 'rejected') && (isOwner || isAuthor)"
        @click="$emit('reopen', pr.id)"
        aria-label="Reopen"
        class="px-4 py-2 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 border border-emerald-500/30 rounded-xl transition-all text-sm flex items-center gap-2"
      >
        <RefreshCw :size="14" />
        {{ $t('templateCollaboration.pullRequests.reopen') }}
      </button>

      <!-- Labels (owner) -->
      <div v-if="isOwner && pr.status === 'open'" class="ml-auto">
        <button
          @click="showLabelPicker = !showLabelPicker"
          aria-label="Labels"
          class="px-3 py-1.5 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg text-xs transition-colors flex items-center gap-1"
        >
          <Tag :size="12" />
          {{ $t('templateCollaboration.pullRequests.labels') }}
        </button>
        <LabelPicker
          v-if="showLabelPicker"
          :model-value="pr.labels || []"
          @update:model-value="$emit('updateLabels', $event); showLabelPicker = false"
          class="mt-2"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import {
  ArrowLeft, GitMerge, Check, X, Plus, Minus, Pencil,
  MessageSquare, MoreHorizontal, Trash2, RefreshCw,
  ShieldAlert, Zap, Tag,
} from 'lucide-vue-next'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import PullRequestStatusBadge from './PullRequestStatusBadge.vue'
import PullRequestDiffView from './PullRequestDiffView.vue'
import PRActivityTimeline from './PRActivityTimeline.vue'
import EmojiReactions from '@/components/common/EmojiReactions.vue'
import LabelPicker from '@/components/common/LabelPicker.vue'

const props = defineProps({
  pr: { type: Object, required: true },
  comments: { type: Array, default: () => [] },
  isOwner: { type: Boolean, default: false },
  currentUserId: { type: String, default: '' },
  mergeCheckData: { type: Object, default: null },
})

const emit = defineEmits([
  'back', 'merge', 'approve', 'reject', 'close', 'reopen', 'ready',
  'comment', 'deleteComment', 'editComment',
  'toggleReaction', 'toggleCommentReaction', 'updateLabels',
])

const newComment = ref('')
const showDiff = ref(false)
const showLabelPicker = ref(false)
const openMenuId = ref(null)
const editingCommentId = ref(null)
const editContent = ref('')

const isAuthor = computed(() => props.currentUserId && props.pr.authorId === props.currentUserId)

const labelColors = {
  enhancement: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
  bugfix: 'bg-red-500/20 text-red-400 border border-red-500/30',
  docs: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
  breaking: 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
  performance: 'bg-purple-500/20 text-purple-400 border border-purple-500/30',
}

function labelClass(label) {
  return labelColors[label] || 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
}

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

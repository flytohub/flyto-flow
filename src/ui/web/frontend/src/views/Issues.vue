<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 relative overflow-hidden">
    <!-- Floating Particles -->
    <div class="absolute inset-0 pointer-events-none overflow-hidden">
      <!-- Larger soft glows -->
      <div class="particle particle-a absolute w-3 h-3 rounded-full bg-red-400/20 dark:bg-red-400/15 blur-[1px]"></div>
      <div class="particle particle-b absolute w-4 h-4 rounded-full bg-orange-400/15 dark:bg-orange-400/12 blur-[2px]"></div>
      <div class="particle particle-c absolute w-2.5 h-2.5 rounded-full bg-red-500/25 dark:bg-red-400/18"></div>
      <div class="particle particle-d absolute w-3.5 h-3.5 rounded-full bg-yellow-400/15 dark:bg-yellow-400/12 blur-[1px]"></div>
      <!-- Medium dots -->
      <div class="particle particle-e absolute w-2 h-2 rounded-full bg-orange-500/25 dark:bg-orange-400/18"></div>
      <div class="particle particle-f absolute w-2.5 h-2.5 rounded-full bg-red-400/20 dark:bg-red-400/15"></div>
      <div class="particle particle-g absolute w-5 h-5 rounded-full bg-red-300/10 dark:bg-red-400/8 blur-[3px]"></div>
      <div class="particle particle-h absolute w-2 h-2 rounded-full bg-orange-400/20 dark:bg-orange-400/15"></div>
      <!-- Extra small accent dots -->
      <div class="particle particle-i absolute w-1.5 h-1.5 rounded-full bg-red-500/30 dark:bg-red-400/20"></div>
      <div class="particle particle-j absolute w-3 h-3 rounded-full bg-yellow-500/12 dark:bg-yellow-400/10 blur-[2px]"></div>
      <div class="particle particle-k absolute w-2 h-2 rounded-full bg-red-400/22 dark:bg-red-400/15"></div>
      <div class="particle particle-l absolute w-4 h-4 rounded-full bg-orange-300/10 dark:bg-orange-400/8 blur-[3px]"></div>
    </div>

    <div class="relative z-10">
      <!-- Hero Header -->
      <WaveHero size="small" variant="purple">
        <div class="max-w-5xl mx-auto px-4">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-3xl font-bold text-white mb-2">{{ $t('issues.title', 'Issues') }}</h1>
              <div class="flex items-center gap-4 text-sm">
                <span class="flex items-center gap-1.5 text-green-400">
                  <span class="w-2 h-2 rounded-full bg-green-400"></span>
                  {{ openCount }} {{ $t('issues.status.open', 'Open') }}
                </span>
                <span class="flex items-center gap-1.5 text-gray-400">
                  <span class="w-2 h-2 rounded-full bg-gray-500"></span>
                  {{ closedCount }} {{ $t('issues.status.closed', 'Closed') }}
                </span>
              </div>
            </div>
            <button
              v-if="isLoggedIn"
              @click="showCreateModal = true"
              class="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-sm font-medium rounded-xl hover:shadow-lg hover:shadow-purple-500/30 transition-all"
            >
              <Plus :size="16" />
              {{ $t('issues.newIssue', 'New Issue') }}
            </button>
          </div>
        </div>
      </WaveHero>

      <div class="max-w-5xl mx-auto px-4 py-8">
        <!-- Detail View -->
        <div v-if="selectedIssue">
          <IssueDetailDrawer
            :issue="selectedIssue"
            :comments="comments"
            :comments-loading="commentsLoading"
            :is-admin="isAdmin"
            :is-logged-in="isLoggedIn"
            :has-upvoted="hasUpvoted(selectedIssue)"
            :current-user="currentUser"
            :format-date="formatDate"
            :can-delete-comment="canDeleteComment"
            @close="closeDetail"
            @update-status="updateIssueStatus"
            @delete="deleteIssue"
            @toggle-upvote="toggleUpvote"
            @delete-comment="deleteComment"
            @open-lightbox="openLightbox"
          >
            <template #comment-form>
              <IssueCommentForm
                v-model="newComment"
                :is-logged-in="isLoggedIn"
                :submitting="submittingComment"
                :images="commentImages"
                :images-uploading="commentImagesUploading"
                @submit="submitComment"
                @paste="handleCommentPaste"
                @image-add="handleCommentImageAdd"
                @image-remove="removeCommentImage"
              />
            </template>
          </IssueDetailDrawer>
        </div>

        <!-- List View -->
        <IssueListView
          v-else
          :issues="issues"
          :loading="loading"
          :current-page="currentPage"
          :total-pages="totalPages"
          :filter-status="filterStatus"
          :filter-type="filterType"
          :sort-by="sortBy"
          :type-dropdown-open="typeDropdownOpen"
          :sort-dropdown-open="sortDropdownOpen"
          :status-tabs="statusTabs"
          :type-options="typeOptions"
          :sort-options="sortOptions"
          :format-date="formatDate"
          @update:filterStatus="filterStatus = $event"
          @update:filterType="filterType = $event"
          @update:sortBy="sortBy = $event"
          @update:currentPage="currentPage = $event"
          @toggle-type-dropdown="typeDropdownOpen = !typeDropdownOpen"
          @toggle-sort-dropdown="sortDropdownOpen = !sortDropdownOpen"
          @close-type-dropdown="typeDropdownOpen = false"
          @close-sort-dropdown="sortDropdownOpen = false"
          @open-detail="openDetail"
        />
      </div>
    </div>

    <!-- Create Issue Modal -->
    <IssueCreateModal
      :show="showCreateModal"
      :form="createForm"
      :type-options="typeOptions"
      :priority-options="priorityOptions"
      :submitting="submitting"
      :images="createImages"
      :images-uploading="createImagesUploading"
      @close="showCreateModal = false"
      @submit="submitIssue"
      @update:form="createForm = $event"
      @paste="handleCreatePaste"
      @image-add="handleCreateImageAdd"
      @image-remove="removeCreateImage"
    />

    <!-- Lightbox -->
    <IssueLightbox
      :show="lightbox.show"
      :images="lightbox.images"
      :index="lightbox.index"
      @close="closeLightbox"
      @prev="lightboxPrev"
      @next="lightboxNext"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus } from 'lucide-vue-next'
import { issuesAPI } from '@/api/issues'
import { authAPI } from '@/api/auth'
import { uploadImage } from '@/api/storage'
import WaveHero from '@/components/common/WaveHero.vue'
import IssueDetailDrawer from './issues/IssueDetailDrawer.vue'
import IssueListView from './issues/IssueListView.vue'
import IssueCreateModal from './issues/IssueCreateModal.vue'
import IssueLightbox from './issues/IssueLightbox.vue'
import IssueCommentForm from './issues/IssueCommentForm.vue'
import { useIssueFilters } from '@/composables/issues/useIssueFilters'

const { t } = useI18n()

// ============== Auth ==============
const currentUser = computed(() => authAPI.getLocalUser())
const isLoggedIn = computed(() => authAPI.isLoggedIn())
const isAdmin = computed(() => currentUser.value?.isAdmin || false)

// ============== Filters & List (composable) ==============
const {
  issues,
  loading,
  total,
  currentPage,
  totalPages,
  openCount,
  closedCount,
  filterStatus,
  filterType,
  sortBy,
  typeDropdownOpen,
  sortDropdownOpen,
  typeDropdownRef,
  sortDropdownRef,
  statusTabs,
  typeOptions,
  priorityOptions,
  sortOptions,
  loadIssues,
  loadStats,
} = useIssueFilters()

// ============== Detail State ==============
const selectedIssue = ref(null)
const comments = ref([])
const commentsLoading = ref(false)
const newComment = ref('')
const submittingComment = ref(false)
const commentImages = ref([])
const commentImagesUploading = ref(false)

// ============== Create State ==============
const showCreateModal = ref(false)
const submitting = ref(false)
const createForm = ref({
  title: '',
  description: '',
  type: 'bug',
  priority: 'medium',
})
const createImages = ref([])
const createImagesUploading = ref(false)

// ============== Lightbox ==============
const lightbox = ref({ show: false, images: [], index: 0 })

function openLightbox(images, index) {
  lightbox.value = { show: true, images, index }
  document.addEventListener('keydown', handleLightboxKey)
}
function closeLightbox() {
  lightbox.value.show = false
  document.removeEventListener('keydown', handleLightboxKey)
}
function lightboxPrev() {
  lightbox.value.index = (lightbox.value.index - 1 + lightbox.value.images.length) % lightbox.value.images.length
}
function lightboxNext() {
  lightbox.value.index = (lightbox.value.index + 1) % lightbox.value.images.length
}
function handleLightboxKey(e) {
  if (e.key === 'Escape') closeLightbox()
  else if (e.key === 'ArrowLeft') lightboxPrev()
  else if (e.key === 'ArrowRight') lightboxNext()
}

// ============== Image Upload ==============
const MAX_IMAGES = 5
const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB

async function uploadFiles(files, targetArray, uploadingRef) {
  const remaining = MAX_IMAGES - targetArray.value.length
  const toUpload = files.slice(0, remaining).filter(f => f.size <= MAX_FILE_SIZE)
  if (!toUpload.length) return

  uploadingRef.value = true
  for (const file of toUpload) {
    try {
      const result = await uploadImage(file, 'issue')
      if (result?.url) {
        targetArray.value = [...targetArray.value, result.url]
      }
    } catch (err) {
      console.error('Upload failed:', err)
    }
  }
  uploadingRef.value = false
}

function handleCreateImageAdd(files) {
  uploadFiles(files, createImages, createImagesUploading)
}
function removeCreateImage(idx) {
  createImages.value = createImages.value.filter((_, i) => i !== idx)
}

function handleCommentImageAdd(files) {
  uploadFiles(files, commentImages, commentImagesUploading)
}
function removeCommentImage(idx) {
  commentImages.value = commentImages.value.filter((_, i) => i !== idx)
}

function handlePasteImages(e, targetArray, uploadingRef) {
  const items = e.clipboardData?.items
  if (!items) return
  const files = []
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) files.push(file)
    }
  }
  if (files.length) {
    e.preventDefault()
    uploadFiles(files, targetArray, uploadingRef)
  }
}
function handleCreatePaste(e) {
  handlePasteImages(e, createImages, createImagesUploading)
}
function handleCommentPaste(e) {
  handlePasteImages(e, commentImages, commentImagesUploading)
}

// ============== Methods ==============
async function openDetail(issue) {
  selectedIssue.value = issue
  await loadComments(issue.id)
}

function closeDetail() {
  selectedIssue.value = null
  comments.value = []
  newComment.value = ''
  commentImages.value = []
}

async function loadComments(issueId) {
  commentsLoading.value = true
  const result = await issuesAPI.listComments(issueId)
  if (result.ok) {
    comments.value = result.comments
  }
  commentsLoading.value = false
}

async function submitIssue() {
  submitting.value = true
  const result = await issuesAPI.create({
    title: createForm.value.title.trim(),
    description: createForm.value.description.trim(),
    type: createForm.value.type,
    priority: createForm.value.priority,
    images: createImages.value,
  })
  if (result.ok) {
    showCreateModal.value = false
    createForm.value = { title: '', description: '', type: 'bug', priority: 'medium' }
    createImages.value = []
    await loadIssues()
    await loadStats()
  }
  submitting.value = false
}

async function toggleUpvote(issueId) {
  if (!isLoggedIn.value) return
  const result = await issuesAPI.toggleUpvote(issueId)
  if (result.ok && selectedIssue.value) {
    selectedIssue.value = result.issue
  }
}

async function submitComment() {
  if (!newComment.value.trim() && !commentImages.value.length) return
  submittingComment.value = true
  const result = await issuesAPI.createComment(selectedIssue.value.id, {
    content: newComment.value.trim(),
    images: commentImages.value,
  })
  if (result.ok) {
    comments.value.push(result.comment)
    newComment.value = ''
    commentImages.value = []
    selectedIssue.value.comment_count = (selectedIssue.value.comment_count || 0) + 1
  }
  submittingComment.value = false
}

async function deleteComment(issueId, commentId) {
  const result = await issuesAPI.deleteComment(issueId, commentId)
  if (result.ok) {
    comments.value = comments.value.filter(c => c.id !== commentId)
    if (selectedIssue.value) {
      selectedIssue.value.comment_count = Math.max(0, (selectedIssue.value.comment_count || 1) - 1)
    }
  }
}

async function updateIssueStatus(issueId, status) {
  const result = await issuesAPI.update(issueId, { status })
  if (result.ok) {
    selectedIssue.value = result.issue
    await loadIssues()
    await loadStats()
  }
}

async function deleteIssue(issueId) {
  const result = await issuesAPI.delete(issueId)
  if (result.ok) {
    closeDetail()
    await loadIssues()
    await loadStats()
  }
}

function canDeleteComment(comment) {
  if (!currentUser.value) return false
  return comment.author_id === currentUser.value.id || isAdmin.value
}

function hasUpvoted(issue) {
  if (!currentUser.value) return false
  return (issue.upvoters || []).includes(currentUser.value.id)
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return t('issues.time.justNow', 'just now')
  if (diffMins < 60) return t('issues.time.minutesAgo', '{n} min ago', { n: diffMins })
  if (diffHours < 24) return t('issues.time.hoursAgo', '{n}h ago', { n: diffHours })
  if (diffDays < 30) return t('issues.time.daysAgo', '{n}d ago', { n: diffDays })
  return date.toLocaleDateString()
}

onUnmounted(() => {
  document.removeEventListener('keydown', handleLightboxKey)
})
</script>

<style scoped>
.particle { will-change: transform; }
.particle-a { animation: driftA 22s ease-in-out infinite; }
.particle-b { animation: driftB 28s ease-in-out infinite; }
.particle-c { animation: driftC 18s ease-in-out infinite; }
.particle-d { animation: driftD 30s ease-in-out infinite; }
.particle-e { animation: driftE 20s ease-in-out infinite; }
.particle-f { animation: driftF 26s ease-in-out infinite; }
.particle-g { animation: driftG 35s ease-in-out infinite; }
.particle-h { animation: driftH 24s ease-in-out infinite; }
.particle-i { animation: driftI 16s ease-in-out infinite; }
.particle-j { animation: driftJ 32s ease-in-out infinite; }
.particle-k { animation: driftK 21s ease-in-out infinite; }
.particle-l { animation: driftL 27s ease-in-out infinite; }

@keyframes driftA {
  0%   { top: 12%; left: 8%; }
  25%  { top: 35%; left: 72%; }
  50%  { top: 68%; left: 25%; }
  75%  { top: 20%; left: 55%; }
  100% { top: 12%; left: 8%; }
}
@keyframes driftB {
  0%   { top: 78%; left: 85%; }
  25%  { top: 15%; left: 40%; }
  50%  { top: 50%; left: 90%; }
  75%  { top: 82%; left: 20%; }
  100% { top: 78%; left: 85%; }
}
@keyframes driftC {
  0%   { top: 45%; left: 5%; }
  25%  { top: 10%; left: 60%; }
  50%  { top: 75%; left: 80%; }
  75%  { top: 55%; left: 30%; }
  100% { top: 45%; left: 5%; }
}
@keyframes driftD {
  0%   { top: 90%; left: 50%; }
  25%  { top: 30%; left: 15%; }
  50%  { top: 5%; left: 75%; }
  75%  { top: 60%; left: 92%; }
  100% { top: 90%; left: 50%; }
}
@keyframes driftE {
  0%   { top: 25%; left: 92%; }
  25%  { top: 70%; left: 45%; }
  50%  { top: 40%; left: 10%; }
  75%  { top: 8%; left: 65%; }
  100% { top: 25%; left: 92%; }
}
@keyframes driftF {
  0%   { top: 60%; left: 35%; }
  25%  { top: 85%; left: 78%; }
  50%  { top: 15%; left: 50%; }
  75%  { top: 42%; left: 8%; }
  100% { top: 60%; left: 35%; }
}
@keyframes driftG {
  0%   { top: 5%; left: 45%; }
  25%  { top: 55%; left: 88%; }
  50%  { top: 88%; left: 35%; }
  75%  { top: 30%; left: 5%; }
  100% { top: 5%; left: 45%; }
}
@keyframes driftH {
  0%   { top: 72%; left: 65%; }
  25%  { top: 18%; left: 25%; }
  50%  { top: 60%; left: 55%; }
  75%  { top: 92%; left: 80%; }
  100% { top: 72%; left: 65%; }
}
@keyframes driftI {
  0%   { top: 38%; left: 48%; }
  25%  { top: 82%; left: 12%; }
  50%  { top: 22%; left: 85%; }
  75%  { top: 65%; left: 38%; }
  100% { top: 38%; left: 48%; }
}
@keyframes driftJ {
  0%   { top: 8%; left: 30%; }
  25%  { top: 48%; left: 75%; }
  50%  { top: 85%; left: 15%; }
  75%  { top: 15%; left: 90%; }
  100% { top: 8%; left: 30%; }
}
@keyframes driftK {
  0%   { top: 55%; left: 18%; }
  25%  { top: 5%; left: 70%; }
  50%  { top: 42%; left: 95%; }
  75%  { top: 88%; left: 42%; }
  100% { top: 55%; left: 18%; }
}
@keyframes driftL {
  0%   { top: 30%; left: 82%; }
  25%  { top: 75%; left: 5%; }
  50%  { top: 10%; left: 42%; }
  75%  { top: 62%; left: 72%; }
  100% { top: 30%; left: 82%; }
}
</style>

<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 relative overflow-hidden">
    <!-- Animated Background -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
      <div class="absolute top-1/2 -left-40 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
      <div class="absolute -bottom-40 right-1/3 w-72 h-72 bg-pink-500/20 rounded-full blur-3xl animate-pulse" style="animation-delay: 2s;"></div>
      <div class="absolute inset-0 bg-[linear-gradient(rgba(139,92,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(139,92,246,0.03)_1px,transparent_1px)] bg-[size:50px_50px]"></div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center min-h-screen">
      <div class="relative">
        <div class="w-20 h-20 border-4 border-purple-500/20 rounded-full"></div>
        <div class="absolute top-0 left-0 w-20 h-20 border-4 border-transparent border-t-purple-500 rounded-full animate-spin"></div>
      </div>
    </div>

    <!-- Not Found -->
    <div v-else-if="!template" class="flex flex-col items-center justify-center min-h-screen text-center px-4 relative">
      <div class="w-24 h-24 bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 flex items-center justify-center mb-6">
        <Package :size="48" class="text-gray-500" />
      </div>
      <h1 class="text-2xl font-bold text-white mb-2">{{ $t('templateDetail.notFound.title') }}</h1>
      <p class="text-gray-400 mb-6">{{ $t('templateDetail.notFound.description') }}</p>
      <button
        @click="router.push('/marketplace')"
        class="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:shadow-lg hover:shadow-purple-500/30 text-white font-medium rounded-xl transition-all"
      >
        {{ $t('templateDetail.notFound.browseMarketplace') }}
      </button>
    </div>

    <!-- Template Detail -->
    <template v-else>
      <!-- Header -->
      <TemplateDetailHeader
        :template-name="translatedName"
        :category-name="template.categoryName"
        :is-own-template="isOwnTemplate"
        :is-installed="template.isInstalled"
        :requires-purchase="requiresPurchase"
        :formatted-price="formatPrice(template.price)"
        :installing="installing"
        :purchasing="purchasing"
        @back="router.back()"
        @share="shareTemplate"
        @edit="editTemplate"
        @run="runTemplate"
        @install="installTemplate"
        @export-yaml="exportTemplateYAML"
      />

      <!-- Hero Section -->
      <TemplateDetailHero
        :name="translatedName"
        :description="translatedDescription"
        :icon-url="template.iconUrl"
        :icon-gradient="iconGradient"
        :category-icon="categoryIcon"
        :is-verified="template.isVerified"
        :is-featured="template.isFeatured"
        :pricing="template.pricing"
        :formatted-price="formatPrice(template.price)"
        :avg-rating="template.avgRating || 0"
        :review-count="template.reviewCount || 0"
        :has-rating="hasRating"
        :downloads="template.downloads"
        :creator-id="template.creatorId"
        :creator-name="template.creatorName"
        :creator-avatar="template.creatorAvatar"
      />

      <!-- Tab Bar -->
      <div class="relative max-w-7xl mx-auto px-4 mt-4">
        <PageTabs v-model="activeTab" :tabs="tabs" />
      </div>

      <!-- Content -->
      <main class="relative max-w-7xl mx-auto px-4 py-8">
        <div class="flex flex-col lg:flex-row gap-8">
          <!-- Main Content -->
          <div class="flex-1 space-y-8">

            <!-- ===== Pull Requests Tab ===== -->
            <template v-if="activeTab === 'pull-requests'">
              <PullRequestDetail
                v-if="selectedPR"
                :pr="selectedPR"
                :comments="prComments"
                :is-owner="isOwnTemplate"
                :current-user-id="currentUserId"
                :merge-check-data="mergeCheckData"
                @back="selectedPR = null; prComments = []"
                @merge="handleMergePR"
                @approve="handleReviewPR($event, 'approve')"
                @reject="handleReviewPR($event, 'reject')"
                @close="handleClosePR"
                @reopen="handleReopenPR"
                @ready="handleMarkPRReady"
                @comment="handleCreatePRComment"
                @deleteComment="handleDeletePRComment"
                @editComment="handleEditPRComment"
                @toggleReaction="handleTogglePRReaction"
                @toggleCommentReaction="handleTogglePRCommentReaction"
                @updateLabels="handleUpdatePRLabels"
              />
              <PullRequestList
                v-else
                :pull-requests="pullRequests"
                :status="prStatusFilter"
                :open-count="template.openPrCount || 0"
                :loading="prLoading"
                @select="selectedPR = $event; loadPRDetail($event.id)"
                @filter-status="filterPRs"
              />
            </template>

            <!-- ===== Issues Tab ===== -->
            <template v-else-if="activeTab === 'issues'">
              <TemplateIssueForm
                v-if="showIssueForm"
                :submitting="issueSubmitting"
                @submit="handleCreateIssue"
                @cancel="showIssueForm = false"
              />
              <TemplateIssueDetail
                v-else-if="selectedIssue"
                :issue="selectedIssue"
                :comments="issueComments"
                :can-close="isOwnTemplate || selectedIssue.authorId === currentUserId"
                :is-upvoted="selectedIssue.upvoters?.includes(currentUserId)"
                :is-owner="isOwnTemplate"
                :current-user-id="currentUserId"
                @back="selectedIssue = null"
                @close="handleCloseIssue"
                @reopen="handleReopenIssue"
                @upvote="handleUpvoteIssue"
                @comment="handleCreateComment"
                @deleteComment="handleDeleteIssueComment"
                @editComment="handleEditIssueComment"
                @toggleReaction="handleToggleIssueReaction"
                @toggleCommentReaction="handleToggleIssueCommentReaction"
              />
              <TemplateIssueList
                v-else
                :issues="templateIssues"
                :status-filter="issueStatusFilter"
                :type-filter="issueTypeFilter"
                :loading="issuesLoading"
                @select="selectIssue"
                @create="showIssueForm = true"
                @filter-status="issueStatusFilter = $event; loadIssues()"
                @filter-type="issueTypeFilter = $event; loadIssues()"
              />
            </template>

            <!-- ===== History Tab ===== -->
            <template v-else-if="activeTab === 'history'">
              <CommitTimeline :commits="commitHistory" :loading="historyLoading" />
            </template>

            <!-- ===== Overview Tab (default) ===== -->
            <template v-else>

            <!-- Video Demo -->
            <section v-if="template.videoUrl" class="group">
              <div class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6 hover:border-purple-500/30 transition-all">
                <h2 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center">
                    <PlayCircle :size="16" class="text-white" />
                  </div>
                  {{ $t('templateDetail.video.title') }}
                </h2>
                <div class="aspect-video rounded-xl overflow-hidden bg-black border border-white/10">
                  <iframe
                    v-if="isYouTubeUrl(template.videoUrl)"
                    :src="getYouTubeEmbedUrl(template.videoUrl)"
                    class="w-full h-full"
                    frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen
                  ></iframe>
                  <video v-else :src="template.videoUrl" controls class="w-full h-full"></video>
                </div>
              </div>
            </section>

            <!-- Usage Instructions -->
            <section v-if="template.usageInstructions" class="group">
              <div class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6 hover:border-emerald-500/30 transition-all">
                <h2 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
                    <BookOpen :size="16" class="text-white" />
                  </div>
                  {{ $t('templateDetail.usageInstructions.title') }}
                </h2>
                <div
                  class="prose prose-invert prose-sm max-w-none"
                  v-html="renderMarkdown(template.usageInstructions)"
                ></div>
              </div>
            </section>

            <!-- Screenshots -->
            <section v-if="template.screenshots?.length" class="group">
              <div class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6 hover:border-blue-500/30 transition-all">
                <h2 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                    <Image :size="16" class="text-white" />
                  </div>
                  {{ $t('templateDetail.screenshots') }}
                </h2>
                <div class="flex gap-4 overflow-x-auto pb-2">
                  <img
                    v-for="(img, idx) in template.screenshots"
                    :key="idx"
                    :src="img"
                    :alt="`Screenshot ${idx + 1}`"
                    class="h-48 rounded-xl border border-white/10 flex-shrink-0 cursor-pointer hover:border-purple-500/50 transition-all"
                    @click="openScreenshot(img)"
                  />
                </div>
              </div>
            </section>

            <!-- Permissions -->
            <section v-if="template.requiredPermissions?.length" class="group">
              <div class="bg-amber-500/10 backdrop-blur-xl rounded-2xl border border-amber-500/30 p-6">
                <h2 class="text-lg font-semibold text-amber-400 mb-4 flex items-center gap-2">
                  <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
                    <AlertTriangle :size="16" class="text-white" />
                  </div>
                  {{ $t('templateDetail.requiredPermissions') }}
                </h2>
                <ul class="space-y-2">
                  <li v-for="perm in template.requiredPermissions" :key="perm" class="flex items-center gap-2 text-amber-300">
                    <Shield :size="14" />
                    {{ perm }}
                  </li>
                </ul>
              </div>
            </section>

            <!-- Locked Workflow Notice -->
            <section v-if="template.mutability === 'locked' && !isOwnTemplate" class="group">
              <div class="bg-purple-500/10 backdrop-blur-xl rounded-2xl border border-purple-500/30 p-6">
                <h2 class="text-lg font-semibold text-purple-400 mb-2 flex items-center gap-2">
                  <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center">
                    <Shield :size="16" class="text-white" />
                  </div>
                  {{ $t('templateDetail.protectedWorkflow.title', 'Protected Workflow') }}
                </h2>
                <p class="text-gray-300 text-sm">
                  {{ $t('templateDetail.protectedWorkflow.description', 'This template\'s workflow logic is protected. You can use this template and provide inputs, but the internal workflow structure is not visible. This protects the author\'s intellectual property while still allowing you to run the automation.') }}
                </p>
              </div>
            </section>

            <!-- Pending Collaboration Requests (owner of locked template) -->
            <section v-if="isOwnTemplate && template.mutability === 'locked' && pendingCollabRequests.length > 0" class="group">
              <div class="bg-amber-500/10 backdrop-blur-xl rounded-2xl border border-amber-500/30 p-6">
                <h2 class="text-lg font-semibold text-amber-400 mb-4 flex items-center gap-2">
                  <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
                    <UsersIcon :size="16" class="text-white" />
                  </div>
                  {{ $t('templateDetail.collabRequest.pendingRequests', 'Collaboration Requests') }}
                  <span class="text-sm font-normal text-amber-400/70">({{ pendingCollabRequests.length }})</span>
                </h2>
                <div class="space-y-3">
                  <div
                    v-for="req in pendingCollabRequests"
                    :key="req.id"
                    class="flex items-center gap-3 p-3 bg-gray-900/50 rounded-xl border border-white/5"
                  >
                    <img
                      v-if="req.requester_avatar"
                      :src="req.requester_avatar"
                      :alt="req.requester_name"
                      class="w-10 h-10 rounded-lg object-cover"
                    />
                    <div
                      v-else
                      class="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center text-white font-bold text-sm"
                    >
                      {{ (req.requester_name || '?').charAt(0).toUpperCase() }}
                    </div>
                    <div class="flex-1 min-w-0">
                      <div class="text-white text-sm font-medium truncate">{{ req.requester_name || 'Anonymous' }}</div>
                      <div v-if="req.message" class="text-gray-400 text-xs truncate">{{ req.message }}</div>
                    </div>
                    <div class="flex gap-2">
                      <button
                        @click="handleResolveCollabRequest(req.id, 'approve')"
                        class="px-3 py-1.5 text-xs font-medium bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 border border-emerald-500/30 rounded-lg transition-all"
                      >
                        {{ $t('common.approve', 'Approve') }}
                      </button>
                      <button
                        @click="handleResolveCollabRequest(req.id, 'reject')"
                        class="px-3 py-1.5 text-xs font-medium bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30 rounded-lg transition-all"
                      >
                        {{ $t('common.decline', 'Decline') }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <!-- Tags -->
            <section v-if="template.tags?.length">
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="tag in template.tags"
                  :key="tag"
                  class="px-3 py-1.5 bg-gray-800/50 border border-white/10 text-gray-300 rounded-full text-sm hover:border-purple-500/50 transition-all cursor-pointer"
                >
                  #{{ tag }}
                </span>
              </div>
            </section>

            <!-- Reviews Section -->
            <section class="group">
              <div class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6 hover:border-pink-500/30 transition-all">
                <div class="flex items-center justify-between mb-6">
                  <h2 class="text-lg font-semibold text-white flex items-center gap-2">
                    <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-pink-500 to-rose-500 flex items-center justify-center">
                      <MessageSquare :size="16" class="text-white" />
                    </div>
                    {{ $t('templateDetail.reviews.title') }}
                    <span class="text-gray-500 font-normal">({{ reviewStats.total }})</span>
                  </h2>
                  <div v-if="hasRating" class="flex items-center gap-2 px-3 py-1.5 bg-amber-500/20 rounded-full border border-amber-500/30">
                    <Star :size="16" class="text-amber-400" fill="currentColor" />
                    <span class="font-semibold text-amber-400">{{ formatRating(template.avgRating) }}</span>
                  </div>
                </div>

                <!-- Review Form -->
                <ReviewForm
                  v-if="isLoggedIn && !userReview && !editingReview"
                  @submit="submitReview"
                  class="mb-6"
                />

                <!-- Edit Review Form -->
                <ReviewForm
                  v-if="editingReview"
                  :existingReview="editingReview"
                  @submit="updateReview"
                  @cancel="cancelEditReview"
                  class="mb-6"
                />

                <!-- Login prompt -->
                <div
                  v-if="!isLoggedIn"
                  class="bg-gray-900/50 border border-white/10 rounded-xl p-6 text-center mb-6"
                >
                  <p class="text-gray-400 mb-4">{{ $t('templateDetail.reviews.loginToReview') }}</p>
                  <button
                    @click="$router.push('/login')"
                    class="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:shadow-lg hover:shadow-purple-500/30 text-white font-medium rounded-xl transition-all"
                  >
                    {{ $t('auth.login') }}
                  </button>
                </div>

                <!-- Reviews List -->
                <div v-if="reviews.length > 0" class="space-y-4">
                  <ReviewCard
                    v-for="review in reviews"
                    :key="review.id"
                    :review="review"
                    @edit="startEditReview"
                    @delete="deleteReview"
                  />
                </div>

                <!-- Empty State -->
                <div v-else-if="!isLoggedIn || userReview" class="text-center py-8">
                  <MessageSquare :size="32" class="mx-auto mb-2 text-gray-600" />
                  <p class="text-gray-400">{{ $t('templateDetail.reviews.noReviews') }}</p>
                  <p class="text-sm text-gray-500">{{ $t('templateDetail.reviews.beFirst') }}</p>
                </div>

                <!-- Load More -->
                <button
                  v-if="reviews.length < reviewStats.total"
                  @click="loadMoreReviews"
                  class="w-full py-3 text-purple-400 hover:bg-purple-500/10 rounded-xl mt-4 transition-all border border-transparent hover:border-purple-500/30"
                >
                  {{ $t('templateDetail.reviews.loadMore') }}
                </button>
              </div>
            </section>

            </template>
            <!-- ===== End Overview Tab ===== -->

          </div>

          <!-- Sidebar -->
          <aside class="w-full lg:w-80 flex-shrink-0 space-y-6">
            <TemplateDetailSidebar
              :version="template.version || '1.0.0'"
              :created-at="template.createdAt"
              :updated-at="template.updatedAt"
              :mutability="template.mutability"
              :category-name="template.categoryName"
              :creator-id="template.creatorId"
              :creator-name="template.creatorName"
              :creator-avatar="template.creatorAvatar"
              :is-own-template="isOwnTemplate"
              :is-collaborator="template.isCollaborator"
              :chat-loading="chatLoading"
              :collab-request-status="collabRequestStatus"
              :collab-request-loading="collabRequestLoading"
              @chat="startChatWithAuthor"
              @report="openReportDialog"
              @request-collab="handleRequestCollab"
            />

            <!-- Contributors -->
            <div v-if="contributors.length" class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6">
              <ContributorList :contributors="contributors" />
            </div>

            <!-- Quick Stats -->
            <div class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6 space-y-3">
              <div class="flex items-center justify-between text-sm">
                <span class="text-gray-500 flex items-center gap-1.5">
                  <GitPullRequestIcon :size="14" /> {{ $t('templateCollaboration.pullRequests.title') }}
                </span>
                <span class="text-white font-medium">{{ template.openPrCount || 0 }}</span>
              </div>
              <div class="flex items-center justify-between text-sm">
                <span class="text-gray-500 flex items-center gap-1.5">
                  <CircleDotIcon :size="14" /> {{ $t('templateCollaboration.templateIssues.title') }}
                </span>
                <span class="text-white font-medium">{{ template.openIssueCount || 0 }}</span>
              </div>
              <div class="flex items-center justify-between text-sm">
                <span class="text-gray-500 flex items-center gap-1.5">
                  <UsersIcon :size="14" /> {{ $t('templateCollaboration.contributors.title') }}
                </span>
                <span class="text-white font-medium">{{ template.contributorCount || 0 }}</span>
              </div>

              <!-- Report Issue Button -->
              <button
                v-if="!isOwnTemplate"
                @click="activeTab = 'issues'; showIssueForm = true"
                class="w-full mt-3 py-2 text-sm text-emerald-400 hover:bg-emerald-500/10 border border-emerald-500/30 rounded-xl transition-all flex items-center justify-center gap-1.5"
              >
                <CircleDotIcon :size="14" />
                {{ $t('templateCollaboration.templateIssues.reportIssue') }}
              </button>
            </div>
          </aside>
        </div>
      </main>
    </template>

    <!-- Report Dialog -->
    <ReportDialog
      v-model="showReportDialog"
      :target-type="ReportTargetType.TEMPLATE"
      :target-id="template?.id || ''"
      ref="reportDialogRef"
      @submit="submitReport"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTemplateReviews } from '@/composables/useTemplateReviews'
import { useTemplateDetail } from '@/composables/templateDetail/useTemplateDetail'
import {
  Package, Folder, Star, AlertTriangle, Shield, Image,
  PlayCircle, BookOpen, MessageSquare,
  Zap, Globe, Database, Bell, Brain, Terminal, ShoppingCart, Share2,
  GitPullRequest as GitPullRequestIcon,
  CircleDot as CircleDotIcon,
  Users as UsersIcon,
  History as HistoryIcon,
  Info as InfoIcon,
} from 'lucide-vue-next'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import ReviewCard from '@/components/reviews/ReviewCard.vue'
import ReviewForm from '@/components/reviews/ReviewForm.vue'
import {
  TemplateDetailHeader,
  TemplateDetailHero,
  TemplateDetailSidebar
} from '@/components/templates/detail'
import { authAPI } from '@/api/auth'
import { reportsAPI, ReportTargetType } from '@/api/reports'
import ReportDialog from '@/components/common/ReportDialog.vue'
import PageTabs from '@/components/common/PageTabs.vue'
import PullRequestList from '@/components/templates/pullRequests/PullRequestList.vue'
import PullRequestDetail from '@/components/templates/pullRequests/PullRequestDetail.vue'
import TemplateIssueList from '@/components/templates/templateIssues/TemplateIssueList.vue'
import TemplateIssueDetail from '@/components/templates/templateIssues/TemplateIssueDetail.vue'
import TemplateIssueForm from '@/components/templates/templateIssues/TemplateIssueForm.vue'
import CommitTimeline from '@/components/templates/collaboration/CommitTimeline.vue'
import ContributorList from '@/components/templates/collaboration/ContributorList.vue'
import { EXTERNAL_URLS } from '@/config/urls'
import { formatCurrency, formatDate, formatCompactNumber, formatRating } from '@/utils/format'

const { t } = useI18n()

const {
  template,
  loading,
  installing,
  purchasing,
  chatLoading,
  activeTab,
  translatedName,
  translatedDescription,
  currentUserId,
  isOwnTemplate,
  isLoggedIn,
  hasRating,
  requiresPurchase,
  collabRequestStatus,
  collabRequestLoading,
  pendingCollabRequests,
  selectedPR,
  prStatusFilter,
  prLoading,
  pullRequests,
  prComments,
  mergeCheckData,
  contributors,
  commitHistory,
  historyLoading,
  selectedIssue,
  issueComments,
  templateIssues,
  issuesLoading,
  showIssueForm,
  issueSubmitting,
  issueStatusFilter,
  issueTypeFilter,
  loadTemplate,
  loadCollabRequestStatus,
  loadPendingCollabRequests,
  handleRequestCollab,
  handleResolveCollabRequest,
  installTemplate,
  runTemplate,
  editTemplate,
  shareTemplate,
  exportTemplateYAML,
  startChatWithAuthor,
  filterPRs,
  loadPRDetail,
  handleMergePR,
  handleReviewPR,
  handleClosePR,
  handleReopenPR,
  handleMarkPRReady,
  handleCreatePRComment,
  handleDeletePRComment,
  handleEditPRComment,
  handleTogglePRReaction,
  handleTogglePRCommentReaction,
  handleUpdatePRLabels,
  loadIssues,
  selectIssue,
  handleCreateIssue,
  handleCloseIssue,
  handleReopenIssue,
  handleUpvoteIssue,
  handleCreateComment,
  handleDeleteIssueComment,
  handleEditIssueComment,
  handleToggleIssueReaction,
  handleToggleIssueCommentReaction,
  loadContributors,
  toast,
  router,
} = useTemplateDetail()

const showReportDialog = ref(false)
const reportDialogRef = ref(null)

const tabs = computed(() => [
  { id: 'overview', label: t('templateCollaboration.tabs.overview'), icon: InfoIcon },
  { id: 'pull-requests', label: t('templateCollaboration.tabs.pullRequests'), icon: GitPullRequestIcon, count: template.value?.openPrCount || undefined },
  { id: 'issues', label: t('templateCollaboration.tabs.issues'), icon: CircleDotIcon, count: template.value?.openIssueCount || undefined },
  { id: 'history', label: t('templateCollaboration.tabs.history'), icon: HistoryIcon },
])

// Reviews - using composable
const {
  reviews,
  reviewStats,
  userReview,
  editingReview,
  loadReviews: loadReviewsBase,
  submitReview: submitReviewBase,
  updateReview: updateReviewBase,
  startEditReview,
  cancelEditReview,
  deleteReview: deleteReviewBase,
  loadMoreReviews: loadMoreReviewsBase
} = useTemplateReviews({
  onSuccess: (msg) => toast.success(t('common.success')),
  onError: (err) => toast.error(err?.message || t('common.error'))
})

const categoryIcons = {
  automation: Zap,
  browser: Globe,
  data: Database,
  notification: Bell,
  ai: Brain,
  devops: Terminal,
  ecommerce: ShoppingCart,
  social: Share2
}

const categoryColors = {
  automation: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
  browser: 'linear-gradient(135deg, #3b82f6 0%, #0ea5e9 100%)',
  data: 'linear-gradient(135deg, #10b981 0%, #14b8a6 100%)',
  notification: 'linear-gradient(135deg, #f59e0b 0%, #f97316 100%)',
  ai: 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)',
  devops: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
  ecommerce: 'linear-gradient(135deg, #f97316 0%, #ef4444 100%)',
  social: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)'
}

const categoryIcon = computed(() => {
  const slug = template.value?.categorySlug || 'other'
  return categoryIcons[slug] || Folder
})

const iconGradient = computed(() => {
  const slug = template.value?.categorySlug || 'other'
  return categoryColors[slug] || 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)'
})

// Template actions provided by useTemplateDetail composable

function openReportDialog() {
  if (!authAPI.isLoggedIn()) {
    router.push('/login')
    return
  }

  if (!template.value?.id) return

  showReportDialog.value = true
}

async function submitReport({ targetType, targetId, reason }) {
  try {
    const result = await reportsAPI.create({
      targetType: targetType,
      targetId: targetId,
      reason: reason
    })

    if (result.ok) {
      toast.success(t('templateDetail.reportSuccess'))
      showReportDialog.value = false
      reportDialogRef.value?.reset()
    } else {
      toast.error(result.error || t('templateDetail.reportFailed'))
      reportDialogRef.value?.reset()
    }
  } catch (err) {
    toast.error(err.message || t('templateDetail.reportFailed'))
    reportDialogRef.value?.reset()
  }
}

function openScreenshot(url) {
  window.open(url, '_blank')
}


function formatPrice(cents) {
  if (!cents) return 'Free'
  return formatCurrency(cents)
}

// Video helpers
const YOUTUBE_HOSTS = new Set([
  'youtube.com',
  'www.youtube.com',
  'm.youtube.com',
  'youtu.be',
  'www.youtu.be',
])
const YOUTUBE_VIDEO_ID = /^[A-Za-z0-9_-]{11}$/

function getYouTubeVideoId(url) {
  if (!url) return ''
  try {
    const parsed = new URL(url)
    if (parsed.protocol !== 'https:' || !YOUTUBE_HOSTS.has(parsed.hostname.toLowerCase())) {
      return ''
    }

    const videoId = parsed.hostname.endsWith('youtu.be')
      ? parsed.pathname.split('/').filter(Boolean)[0]
      : parsed.pathname === '/watch'
        ? parsed.searchParams.get('v')
        : ''
    return YOUTUBE_VIDEO_ID.test(videoId || '') ? videoId : ''
  } catch {
    return ''
  }
}

function isYouTubeUrl(url) {
  return Boolean(getYouTubeVideoId(url))
}

function getYouTubeEmbedUrl(url) {
  const videoId = getYouTubeVideoId(url)
  return videoId ? `${EXTERNAL_URLS.YOUTUBE_EMBED}${encodeURIComponent(videoId)}` : ''
}

// Markdown helpers
function renderMarkdown(content) {
  if (!content) return ''
  const html = marked(content)
  return DOMPurify.sanitize(html)
}

// Review wrapper functions - pass templateId to composable
function loadReviews() {
  return loadReviewsBase(template.value?.id)
}

function submitReview(data) {
  return submitReviewBase(template.value?.id, data)
}

function updateReview(data) {
  return updateReviewBase(template.value?.id, data)
}

async function deleteReview(reviewId) {
  if (!confirm(t('common.confirm'))) return
  return deleteReviewBase(reviewId)
}

function loadMoreReviews() {
  return loadMoreReviewsBase(template.value?.id)
}

// PR, Issue, Collaboration methods provided by useTemplateDetail composable

onMounted(async () => {
  await loadTemplate()
  if (template.value) {
    await loadReviews()
    loadContributors()
    loadCollabRequestStatus()
    loadPendingCollabRequests()
  }
})
</script>

<style scoped>
.prose :deep(h1) { @apply text-xl font-bold mb-4 text-white; }
.prose :deep(h2) { @apply text-lg font-semibold mb-3 text-white; }
.prose :deep(h3) { @apply text-base font-medium mb-2 text-white; }
.prose :deep(p) { @apply mb-3 text-gray-300; }
.prose :deep(ul) { @apply list-disc pl-5 mb-3 text-gray-300; }
.prose :deep(ol) { @apply list-decimal pl-5 mb-3 text-gray-300; }
.prose :deep(li) { @apply mb-1; }
.prose :deep(code) { @apply bg-purple-500/20 text-purple-300 px-1.5 py-0.5 rounded text-sm; }
.prose :deep(pre) { @apply bg-gray-900 p-4 rounded-lg overflow-x-auto mb-3 border border-white/10; }
.prose :deep(blockquote) { @apply border-l-4 border-purple-500 pl-4 italic text-gray-400; }
.prose :deep(a) { @apply text-purple-400 hover:text-purple-300 underline; }
</style>

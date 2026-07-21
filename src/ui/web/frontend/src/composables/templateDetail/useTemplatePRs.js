/**
 * Template Pull Requests Composable
 *
 * Extracted from useTemplateDetail.js — handles all PR-related state and actions.
 */

import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { templatesAPI } from '@/api/templates'
import { useToast } from '@/composables/useToast'

/**
 * @param {Object} options
 * @param {import('vue').Ref} options.template - Template ref
 * @param {Function} options.loadTemplate - Reload template data
 */
export function useTemplatePRs({ template, loadTemplate }) {
  const { t } = useI18n()
  const toast = useToast()

  const selectedPR = ref(null)
  const prStatusFilter = ref(null)
  const prLoading = ref(false)
  const pullRequests = ref([])
  const prComments = ref([])
  const mergeCheckData = ref(null)
  const contributors = ref([])
  const commitHistory = ref([])
  const historyLoading = ref(false)

  async function loadPRs() {
    if (!template.value?.id) return
    prLoading.value = true
    try {
      const result = await templatesAPI.listPullRequests(template.value.id, { status: prStatusFilter.value })
      if (result.ok) pullRequests.value = result.pull_requests || []
    } catch (err) { console.warn('[templatePRs]', err) }
    finally { prLoading.value = false }
  }

  function filterPRs(status) {
    prStatusFilter.value = status
    loadPRs()
  }

  async function loadPRDetail(prId) {
    if (!template.value?.id) return
    try {
      const [prResult, commentsResult, checkResult] = await Promise.all([
        templatesAPI.getPullRequest(template.value.id, prId),
        templatesAPI.listPRComments(template.value.id, prId),
        templatesAPI.mergeCheck(template.value.id, prId),
      ])
      if (prResult.ok) selectedPR.value = prResult.pull_request
      if (commentsResult.ok) prComments.value = commentsResult.comments || []
      if (checkResult.ok) mergeCheckData.value = checkResult
    } catch (err) { console.warn('[templatePRs]', err) }
  }

  async function handleMergePR(prId) {
    try {
      const result = await templatesAPI.mergePullRequest(template.value.id, prId)
      if (result.ok) {
        toast.success(t('templateCollaboration.pullRequests.mergeSuccess'))
        selectedPR.value = null
        prComments.value = []
        await loadPRs()
        await loadTemplate()
      }
    } catch (err) { toast.error(err.message) }
  }

  async function handleReviewPR(prId, action) {
    try {
      const result = await templatesAPI.reviewPullRequest(template.value.id, prId, { action })
      if (result.ok) {
        toast.success(action === 'approve' ? t('templateCollaboration.pullRequests.approved') : t('templateCollaboration.pullRequests.rejected'))
        if (result.pull_request) selectedPR.value = result.pull_request
        await loadPRs()
      }
    } catch (err) { toast.error(err.message) }
  }

  async function handleClosePR(prId) {
    try {
      const result = await templatesAPI.closePullRequest(template.value.id, prId)
      if (result.ok) {
        toast.success(t('templateCollaboration.pullRequests.closed'))
        selectedPR.value = null
        prComments.value = []
        await loadPRs()
      }
    } catch (err) { toast.error(err.message) }
  }

  async function handleReopenPR(prId) {
    try {
      const result = await templatesAPI.reopenPullRequest(template.value.id, prId)
      if (result.ok) {
        toast.success(t('templateCollaboration.pullRequests.reopened'))
        if (result.pull_request) selectedPR.value = result.pull_request
        await loadPRs()
      }
    } catch (err) { toast.error(err.message) }
  }

  async function handleMarkPRReady(prId) {
    try {
      const result = await templatesAPI.markPRReady(template.value.id, prId)
      if (result.ok) {
        toast.success(t('templateCollaboration.pullRequests.markedReady'))
        if (result.pull_request) selectedPR.value = result.pull_request
        await loadPRs()
      }
    } catch (err) { toast.error(err.message) }
  }

  async function handleCreatePRComment(content) {
    if (!selectedPR.value) return
    try {
      const result = await templatesAPI.createPRComment(template.value.id, selectedPR.value.id, { content })
      if (result.ok && result.comment) {
        prComments.value.push(result.comment)
      }
    } catch (err) { toast.error(err.message) }
  }

  async function handleDeletePRComment(commentId) {
    if (!selectedPR.value || !confirm(t('templateCollaboration.comments.deleteConfirm'))) return
    try {
      const result = await templatesAPI.deletePRComment(template.value.id, selectedPR.value.id, commentId)
      if (result.ok) {
        prComments.value = prComments.value.filter(c => c.id !== commentId)
      }
    } catch (err) { toast.error(err.message) }
  }

  async function handleEditPRComment({ commentId, content }) {
    if (!selectedPR.value) return
    try {
      const result = await templatesAPI.updatePRComment(template.value.id, selectedPR.value.id, commentId, { content })
      if (result.ok && result.comment) {
        const idx = prComments.value.findIndex(c => c.id === commentId)
        if (idx >= 0) prComments.value[idx] = result.comment
      }
    } catch (err) { toast.error(err.message) }
  }

  async function handleTogglePRReaction({ type }) {
    if (!selectedPR.value) return
    try {
      const result = await templatesAPI.togglePRReaction(template.value.id, selectedPR.value.id, type)
      if (result.ok) selectedPR.value = { ...selectedPR.value, reactions: result.reactions }
    } catch (err) { console.warn('[templatePRs]', err) }
  }

  async function handleTogglePRCommentReaction({ commentId, type }) {
    if (!selectedPR.value) return
    try {
      const result = await templatesAPI.togglePRCommentReaction(template.value.id, selectedPR.value.id, commentId, type)
      if (result.ok) {
        const idx = prComments.value.findIndex(c => c.id === commentId)
        if (idx >= 0) prComments.value[idx] = { ...prComments.value[idx], reactions: result.reactions }
      }
    } catch (err) { console.warn('[templatePRs]', err) }
  }

  async function handleUpdatePRLabels(labels) {
    if (!selectedPR.value) return
    try {
      const result = await templatesAPI.updatePRLabels(template.value.id, selectedPR.value.id, labels)
      if (result.ok && result.pull_request) selectedPR.value = result.pull_request
    } catch (err) { toast.error(err.message) }
  }

  return {
    selectedPR,
    prStatusFilter,
    prLoading,
    pullRequests,
    prComments,
    mergeCheckData,
    contributors,
    commitHistory,
    historyLoading,
    loadPRs,
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
  }
}

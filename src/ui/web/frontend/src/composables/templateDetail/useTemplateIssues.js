/**
 * Template Issues Composable
 *
 * Extracted from useTemplateDetail.js — handles all issue-related state and actions.
 */

import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { templatesAPI } from '@/api/templates'
import { useToast } from '@/composables/useToast'

/**
 * @param {Object} options
 * @param {import('vue').Ref} options.template - Template ref
 */
export function useTemplateIssues({ template }) {
  const { t } = useI18n()
  const toast = useToast()

  const selectedIssue = ref(null)
  const issueComments = ref([])
  const templateIssues = ref([])
  const issuesLoading = ref(false)
  const showIssueForm = ref(false)
  const issueSubmitting = ref(false)
  const issueStatusFilter = ref(null)
  const issueTypeFilter = ref(null)

  async function loadIssues() {
    if (!template.value?.id) return
    issuesLoading.value = true
    try {
      const result = await templatesAPI.listTemplateIssues(template.value.id, {
        status: issueStatusFilter.value,
        type: issueTypeFilter.value,
      })
      if (result.ok) templateIssues.value = result.issues || []
    } catch (err) { console.warn('[templateIssues]', err) }
    finally { issuesLoading.value = false }
  }

  async function selectIssue(issue) {
    selectedIssue.value = issue
    try {
      const result = await templatesAPI.listTemplateIssueComments(template.value.id, issue.id)
      if (result.ok) issueComments.value = result.comments || []
    } catch (err) { console.warn('[templateIssues]', err) }
  }

  async function handleCreateIssue(data) {
    issueSubmitting.value = true
    try {
      const result = await templatesAPI.createTemplateIssue(template.value.id, data)
      if (result.ok) {
        toast.success(t('templateCollaboration.templateIssues.created'))
        showIssueForm.value = false
        await loadIssues()
      }
    } catch (err) { toast.error(err.message) }
    finally { issueSubmitting.value = false }
  }

  async function handleCloseIssue(issueId) {
    try {
      const result = await templatesAPI.closeTemplateIssue(template.value.id, issueId)
      if (result.ok) {
        toast.success(t('templateCollaboration.templateIssues.issueClosed'))
        selectedIssue.value = null
        await loadIssues()
      }
    } catch (err) { toast.error(err.message) }
  }

  async function handleReopenIssue(issueId) {
    try {
      const result = await templatesAPI.reopenTemplateIssue(template.value.id, issueId)
      if (result.ok) {
        toast.success(t('templateCollaboration.templateIssues.issueReopened'))
        if (result.issue) selectedIssue.value = result.issue
        await loadIssues()
      }
    } catch (err) { toast.error(err.message) }
  }

  async function handleUpvoteIssue(issueId) {
    try {
      const result = await templatesAPI.toggleTemplateIssueUpvote(template.value.id, issueId)
      if (result.ok && result.issue) selectedIssue.value = result.issue
    } catch (err) { console.warn('[templateIssues]', err) }
  }

  async function handleCreateComment(content) {
    if (!selectedIssue.value) return
    try {
      const result = await templatesAPI.createTemplateIssueComment(
        template.value.id, selectedIssue.value.id, { content }
      )
      if (result.ok && result.comment) {
        issueComments.value.push(result.comment)
      }
    } catch (err) { toast.error(err.message) }
  }

  async function handleDeleteIssueComment(commentId) {
    if (!selectedIssue.value || !confirm(t('templateCollaboration.comments.deleteConfirm'))) return
    try {
      const result = await templatesAPI.deleteTemplateIssueComment(template.value.id, selectedIssue.value.id, commentId)
      if (result.ok) {
        issueComments.value = issueComments.value.filter(c => c.id !== commentId)
      }
    } catch (err) { toast.error(err.message) }
  }

  async function handleEditIssueComment({ commentId, content }) {
    if (!selectedIssue.value) return
    try {
      const result = await templatesAPI.updateTemplateIssueComment(template.value.id, selectedIssue.value.id, commentId, { content })
      if (result.ok && result.comment) {
        const idx = issueComments.value.findIndex(c => c.id === commentId)
        if (idx >= 0) issueComments.value[idx] = result.comment
      }
    } catch (err) { toast.error(err.message) }
  }

  async function handleToggleIssueReaction({ type }) {
    if (!selectedIssue.value) return
    try {
      const result = await templatesAPI.toggleIssueReaction(template.value.id, selectedIssue.value.id, type)
      if (result.ok) selectedIssue.value = { ...selectedIssue.value, reactions: result.reactions }
    } catch (err) { console.warn('[templateIssues]', err) }
  }

  async function handleToggleIssueCommentReaction({ commentId, type }) {
    if (!selectedIssue.value) return
    try {
      const result = await templatesAPI.toggleIssueCommentReaction(template.value.id, selectedIssue.value.id, commentId, type)
      if (result.ok) {
        const idx = issueComments.value.findIndex(c => c.id === commentId)
        if (idx >= 0) issueComments.value[idx] = { ...issueComments.value[idx], reactions: result.reactions }
      }
    } catch (err) { console.warn('[templateIssues]', err) }
  }

  return {
    selectedIssue,
    issueComments,
    templateIssues,
    issuesLoading,
    showIssueForm,
    issueSubmitting,
    issueStatusFilter,
    issueTypeFilter,
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
  }
}

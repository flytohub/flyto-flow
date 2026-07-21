/**
 * Template Detail Composable
 *
 * Orchestrates template detail page: core template data, installation,
 * collaboration requests, PRs (useTemplatePRs), and issues (useTemplateIssues).
 */

import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { templatesAPI } from '@/api/templates'
import { resolveTranslated } from '@/api/templates/helpers'
import { useToast } from '@/composables/useToast'
import { authAPI } from '@/api/auth'
import { post, get } from '@/api/client'
import { ENDPOINTS } from '@/api/config'
import { redirectToCheckout } from '@/api/payment'
import {
  requestCollaboration,
  getMyRequestStatus,
  listCollaborationRequests,
  resolveCollaborationRequest,
} from '@/api/collaborationRequests'

import { useTemplatePRs } from './useTemplatePRs'
import { useTemplateIssues } from './useTemplateIssues'

export function useTemplateDetail() {
  const router = useRouter()
  const route = useRoute()
  const { t, locale } = useI18n()
  const toast = useToast()

  const template = ref(null)
  const loading = ref(true)
  const installing = ref(false)
  const purchasing = ref(false)
  const chatLoading = ref(false)

  // Tab system
  const activeTab = ref('overview')

  // Collaboration request state
  const collabRequestStatus = ref(null)
  const collabRequestLoading = ref(false)
  const pendingCollabRequests = ref([])
  const collabRequestsLoading = ref(false)

  const translatedName = computed(() => {
    const tmpl = template.value
    if (!tmpl) return ''
    return resolveTranslated(tmpl.translations, locale.value, 'name', tmpl.name)
  })
  const translatedDescription = computed(() => {
    const tmpl = template.value
    if (!tmpl) return ''
    return resolveTranslated(tmpl.translations, locale.value, 'description', tmpl.description)
  })

  const currentUserId = computed(() => {
    const user = authAPI.getLocalUser()
    return user?.uid || ''
  })

  const isOwnTemplate = computed(() => {
    const currentUser = authAPI.getLocalUser()
    return currentUser && template.value?.creatorId === currentUser.uid
  })

  const isLoggedIn = computed(() => !!authAPI.getLocalUser())

  const hasRating = computed(() => {
    return template.value?.avgRating > 0 && template.value?.reviewCount > 0
  })

  const requiresPurchase = computed(() => {
    if (!template.value) return false
    if (isOwnTemplate.value) return false
    if (template.value.pricing === 'free') return false
    if (template.value.isInstalled) return false
    if (template.value.hasAccess) return false
    return true
  })

  // ===== Core Template Actions =====

  async function loadTemplate() {
    loading.value = true
    try {
      const id = route.params.id
      const response = await templatesAPI.getTemplate(id)

      if (!response.ok || !response.template) {
        template.value = null
        return
      }

      const data = response.template
      template.value = {
        ...data,
        avgRating: data.ratingCount > 0 ? (data.ratingSum / data.ratingCount) : 0,
        reviewCount: data.ratingCount || 0
      }
    } catch (err) {
      template.value = null
    } finally {
      loading.value = false
    }
  }

  // ===== Collaboration Requests =====

  async function loadCollabRequestStatus() {
    if (!template.value || isOwnTemplate.value || !isLoggedIn.value) return
    if (template.value.mutability !== 'locked') return
    if (template.value.isCollaborator) return
    try {
      const res = await getMyRequestStatus(template.value.id)
      collabRequestStatus.value = res.request?.status || null
    } catch {
      // Ignore errors
    }
  }

  async function loadPendingCollabRequests() {
    if (!template.value || !isOwnTemplate.value) return
    if (template.value.mutability !== 'locked') return
    collabRequestsLoading.value = true
    try {
      const res = await listCollaborationRequests(template.value.id, 'pending')
      pendingCollabRequests.value = res.requests || []
    } catch {
      // Ignore errors
    } finally {
      collabRequestsLoading.value = false
    }
  }

  async function handleRequestCollab() {
    if (!template.value) return
    collabRequestLoading.value = true
    try {
      await requestCollaboration(template.value.id)
      collabRequestStatus.value = 'pending'
      toast.success(t('templateDetail.collabRequest.sent', 'Collaboration request sent'))
    } catch (err) {
      toast.error(err.message || t('common.error'))
    } finally {
      collabRequestLoading.value = false
    }
  }

  async function handleResolveCollabRequest(requestId, action) {
    try {
      await resolveCollaborationRequest(requestId, action)
      pendingCollabRequests.value = pendingCollabRequests.value.filter(r => r.id !== requestId)
      const msg = action === 'approve'
        ? t('templateDetail.collabRequest.approved', 'Request approved')
        : t('templateDetail.collabRequest.rejected', 'Request declined')
      toast.success(msg)
    } catch (err) {
      toast.error(err.message || t('common.error'))
    }
  }

  // ===== Install / Purchase / Navigation =====

  async function installTemplate() {
    if (!template.value) return
    if (requiresPurchase.value) {
      await purchaseTemplate()
      return
    }
    installing.value = true
    try {
      const result = await templatesAPI.addToLibrary(template.value.id, 'installed')
      if (!result.ok) {
        throw new Error(result.error || t('marketplace.installFailed'))
      }
      template.value.isInstalled = true
      toast.success(t('marketplace.installSuccess'))
    } catch (err) {
      toast.error(err.message || t('marketplace.installFailed'))
    } finally {
      installing.value = false
    }
  }

  async function purchaseTemplate() {
    if (!template.value) return
    if (!isLoggedIn.value) {
      router.push('/login')
      return
    }
    purchasing.value = true
    try {
      await redirectToCheckout(template.value.id)
    } catch (err) {
      toast.error(err.message || t('payment.errors.failed'))
      purchasing.value = false
    }
  }

  function runTemplate() {
    if (!template.value) return
    router.push(`/templates/builder/${template.value.id}`)
  }

  function editTemplate() {
    if (!template.value) return
    router.push(`/templates/builder/${template.value.id}`)
  }

  function shareTemplate() {
    const url = window.location.href
    navigator.clipboard.writeText(url)
    toast.success(t('common.linkCopied'))
  }

  async function exportTemplateYAML() {
    if (!template.value?.id) return
    try {
      const result = await templatesAPI.exportYAML(template.value.id)
      if (!result.ok) {
        toast.error(result.error || 'Export failed')
        return
      }
      const blob = new Blob([result.yaml], { type: 'application/x-yaml' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = result.filename || `${template.value.name || 'template'}.yaml`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      toast.success('YAML exported')
    } catch (err) {
      toast.error(err.message || 'Export failed')
    }
  }

  async function startChatWithAuthor() {
    if (!authAPI.isLoggedIn()) {
      router.push('/login')
      return
    }
    if (!template.value?.creatorId) return
    chatLoading.value = true
    try {
      const conversation = await post(ENDPOINTS.CHAT.CONVERSATIONS, {
        participantIds: [template.value.creatorId]
      })
      router.push(`/messages?conversation=${conversation.id}`)
    } catch (err) {
      toast.error(t('chat.startChatFailed'))
    } finally {
      chatLoading.value = false
    }
  }

  // ===== Sub-composables =====

  const prComposable = useTemplatePRs({ template, loadTemplate })
  const issuesComposable = useTemplateIssues({ template })

  // ===== History & Contributors =====

  async function loadContributors() {
    if (!template.value?.id) return
    try {
      const result = await get(`/templates/${template.value.id}/contributors`)
      if (result.ok) prComposable.contributors.value = result.contributors || []
    } catch (err) { console.warn('[templateDetail]', err) }
  }

  async function loadCommitHistory() {
    if (!template.value?.id) return
    prComposable.historyLoading.value = true
    try {
      const result = await get(`/templates/${template.value.id}/commit-history`)
      if (result.ok) prComposable.commitHistory.value = result.commits || []
    } catch (err) { console.warn('[templateDetail]', err) }
    finally { prComposable.historyLoading.value = false }
  }

  // Watch tab changes to lazy-load data
  watch(activeTab, (tab) => {
    if (tab === 'pull-requests' && !prComposable.pullRequests.value.length) prComposable.loadPRs()
    if (tab === 'issues' && !issuesComposable.templateIssues.value.length) issuesComposable.loadIssues()
    if (tab === 'history' && !prComposable.commitHistory.value.length) loadCommitHistory()
  })

  return {
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
    // Collaboration requests
    collabRequestStatus,
    collabRequestLoading,
    pendingCollabRequests,
    collabRequestsLoading,
    // PR state (spread from sub-composable)
    ...prComposable,
    // Issues state (spread from sub-composable)
    ...issuesComposable,
    // Methods
    loadTemplate,
    loadCollabRequestStatus,
    loadPendingCollabRequests,
    handleRequestCollab,
    handleResolveCollabRequest,
    installTemplate,
    purchaseTemplate,
    runTemplate,
    editTemplate,
    shareTemplate,
    exportTemplateYAML,
    startChatWithAuthor,
    loadContributors,
    loadCommitHistory,
    toast,
    router,
    route,
  }
}

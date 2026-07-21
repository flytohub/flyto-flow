import { ref, watch, nextTick } from 'vue'
import { get, post } from '@/api/client'

/**
 * Join collaboration panel logic
 * @param {Object} options
 * @param {import('vue-router').Router} options.router - Vue Router instance
 * @param {Function} options.t - i18n translation function
 */
export function useJoinCollaboration({ router, t }) {
  const showJoinInput = ref(false)
  const joinCode = ref('')
  const joinError = ref('')
  const joinSuccess = ref(false)
  const isJoiningCollab = ref(false)
  const joinInputRef = ref(null)

  watch(showJoinInput, async (v) => {
    if (v) {
      joinError.value = ''
      joinSuccess.value = false
      await nextTick()
      joinInputRef.value?.focus()
    }
  })

  function closeJoinPanel() {
    showJoinInput.value = false
    joinCode.value = ''
    joinError.value = ''
    joinSuccess.value = false
  }

  async function handleJoinCollaboration() {
    const code = joinCode.value.trim()
    if (!code) return

    isJoiningCollab.value = true
    joinError.value = ''
    joinSuccess.value = false

    try {
      // Step 1: resolve code
      const resolveData = await get(`/collaboration/resolve-code/${encodeURIComponent(code)}`)
      if (!resolveData || resolveData.error) {
        joinError.value = resolveData?.error || t('collaboration.invite.invalidCode')
        return
      }

      // Step 2: request to join
      const joinData = await post('/collaboration/join', { code })
      if (!joinData || joinData.error) {
        joinError.value = joinData?.error || t('collaboration.invite.joinFailed')
        return
      }

      const data = await joinRes.json()

      if (data.status === 'approved') {
        // Show success state briefly, then navigate
        joinSuccess.value = true
        setTimeout(() => {
          router.push({
            path: `/templates/builder/${data.workflow_id}`,
            query: { invite: code },
          })
        }, 800)
      } else {
        // Pending approval
        joinError.value = t('collaboration.invite.pendingApproval')
        joinCode.value = ''
      }
    } catch {
      joinError.value = t('collaboration.invite.joinFailed')
    } finally {
      isJoiningCollab.value = false
    }
  }

  return {
    showJoinInput,
    joinCode,
    joinError,
    joinSuccess,
    isJoiningCollab,
    joinInputRef,
    closeJoinPanel,
    handleJoinCollaboration,
  }
}

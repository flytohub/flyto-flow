/**
 * HTTP Auth State Management
 *
 * Manages auth type switching (none/credential/bearer/basic/apiKey)
 * and auth field state for HTTP node params.
 */
import { ref } from 'vue'

export function useHttpAuth(localParams, emitUpdate) {
  const authType = ref('none')
  const authToken = ref('')
  const authUsername = ref('')
  const authPassword = ref('')
  const authKeyName = ref('X-API-Key')
  const authKeyValue = ref('')
  const selectedCredential = ref('')

  function initAuth() {
    if (localParams.value.auth) {
      authType.value = localParams.value.auth.type || 'none'
      if (authType.value === 'bearer') {
        authToken.value = localParams.value.auth.token || ''
      } else if (authType.value === 'basic') {
        authUsername.value = localParams.value.auth.username || ''
        authPassword.value = localParams.value.auth.password || ''
      } else if (authType.value === 'apiKey') {
        authKeyName.value = localParams.value.auth.name || 'X-API-Key'
        authKeyValue.value = localParams.value.auth.value || ''
      } else if (authType.value === 'credential') {
        selectedCredential.value = localParams.value.auth.credentialName || ''
      }
    } else {
      authType.value = 'none'
    }
  }

  function updateAuth() {
    if (authType.value === 'none') {
      localParams.value.auth = null
    } else if (authType.value === 'credential') {
      localParams.value.auth = { type: 'credential', credentialName: selectedCredential.value }
    } else if (authType.value === 'bearer') {
      localParams.value.auth = { type: 'bearer', token: authToken.value }
    } else if (authType.value === 'basic') {
      localParams.value.auth = { type: 'basic', username: authUsername.value, password: authPassword.value }
    } else if (authType.value === 'apiKey') {
      localParams.value.auth = { type: 'api_key', name: authKeyName.value, value: authKeyValue.value }
    }
    emitUpdate()
  }

  function onAuthTypeChange() {
    updateAuth()
  }

  function onCredentialChange(credName) {
    selectedCredential.value = credName
    updateAuth()
  }

  return {
    authType,
    authToken,
    authUsername,
    authPassword,
    authKeyName,
    authKeyValue,
    selectedCredential,
    initAuth,
    updateAuth,
    onAuthTypeChange,
    onCredentialChange
  }
}

/**
 * GitHub OAuth integration (popup-based authorization code flow)
 *
 * Opens a popup to GitHub OAuth, then GitHub redirects back to /github-callback
 * which sends the authorization code back via postMessage.
 *
 * Client ID is provided at runtime from the cloud auth config endpoint,
 * with fallback to VITE_GITHUB_CLIENT_ID for local dev.
 */

const GITHUB_AUTH_URL = 'https://github.com/login/oauth/authorize'

let _clientId = import.meta.env.VITE_GITHUB_CLIENT_ID || null

/**
 * Set GitHub client ID from cloud auth config (runtime).
 * @param {string} clientId
 */
export function setGithubClientId(clientId) {
  if (clientId) _clientId = clientId
}

/**
 * Check if GitHub OAuth is configured
 * @returns {boolean}
 */
export function isGithubAuthEnabled() {
  return !!_clientId
}

/**
 * Open GitHub OAuth popup and return the authorization code.
 * @returns {Promise<string>} authorization code
 */
export function requestGithubCredential() {
  return new Promise((resolve, reject) => {
    if (!_clientId) {
      reject(new Error('GitHub OAuth not configured'))
      return
    }

    const redirectUri = `${window.location.origin}/github-callback`
    const scope = 'user:email'
    const state = crypto.randomUUID()

    sessionStorage.setItem('github_oauth_state', state)

    const width = 500
    const height = 700
    const left = window.screenX + (window.outerWidth - width) / 2
    const top = window.screenY + (window.outerHeight - height) / 2

    const url = `${GITHUB_AUTH_URL}?client_id=${_clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${scope}&state=${state}`

    const popup = window.open(url, 'github-oauth', `width=${width},height=${height},left=${left},top=${top}`)

    if (!popup) {
      reject(new Error('Popup blocked'))
      return
    }

    let settled = false

    function cleanup() {
      window.removeEventListener('message', handleMessage)
      clearInterval(pollTimer)
      clearInterval(storagePollTimer)
      clearTimeout(timeoutTimer)
    }

    function processResult(data) {
      if (settled) return
      settled = true
      cleanup()

      const { code, error, state: returnedState } = data

      if (error) {
        reject(new Error(error))
        return
      }

      const savedState = sessionStorage.getItem('github_oauth_state')
      sessionStorage.removeItem('github_oauth_state')

      if (!savedState || savedState !== returnedState) {
        reject(new Error('Invalid state parameter'))
        return
      }

      resolve(code)
    }

    // Primary path: postMessage from popup
    function handleMessage(event) {
      if (event.origin !== window.location.origin) return
      if (event.data?.type !== 'github-oauth-callback') return
      processResult(event.data)
    }

    window.addEventListener('message', handleMessage)

    // COOP fallback: poll localStorage for result
    const storagePollTimer = setInterval(() => {
      try {
        const raw = localStorage.getItem('github_oauth_result')
        if (raw) {
          localStorage.removeItem('github_oauth_result')
          const data = JSON.parse(raw)
          if (data?.type === 'github-oauth-callback') {
            processResult(data)
          }
        }
      } catch {
        // ignore parse errors
      }
    }, 500)

    // Popup closed detection — delay 1s to allow message/storage to arrive
    const pollTimer = setInterval(() => {
      if (popup.closed) {
        clearInterval(pollTimer)
        setTimeout(() => {
          if (!settled) {
            settled = true
            cleanup()
            reject(null)
          }
        }, 1000)
      }
    }, 500)

    // Global timeout: 120 seconds
    const timeoutTimer = setTimeout(() => {
      if (!settled) {
        settled = true
        cleanup()
        try { popup.close() } catch {}
        reject(new Error('GitHub login timed out'))
      }
    }, 120000)
  })
}

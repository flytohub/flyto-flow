<template>
  <div class="min-h-screen flex items-center justify-center bg-[#0a0a0f]">
    <div class="text-center">
      <div class="w-8 h-8 border-2 border-white/20 border-t-purple-400 rounded-full animate-spin"></div>
      <p class="text-white/60 text-sm mt-3">Completing GitHub login...</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  const params = new URLSearchParams(window.location.search)
  const code = params.get('code')
  const state = params.get('state')
  const error = params.get('error')

  const message = {
    type: 'github-oauth-callback',
    code,
    state,
    error: error || (code ? null : 'No authorization code received'),
  }

  if (window.opener) {
    // Primary path: postMessage to opener window
    window.opener.postMessage(message, window.location.origin)
  } else {
    // COOP fallback: opener blocked by Cross-Origin-Opener-Policy
    try {
      localStorage.setItem('github_oauth_result', JSON.stringify(message))
    } catch {
      // localStorage unavailable, nothing we can do
    }
  }

  setTimeout(() => window.close(), 300)
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-[#0a0a0f] px-4">
    <div class="w-full max-w-md rounded-2xl border border-white/10 bg-white/[0.03] p-8 text-center">
      <!-- Loading -->
      <div v-if="loading" class="py-6">
        <div class="w-8 h-8 mx-auto border-2 border-white/20 border-t-purple-400 rounded-full animate-spin"></div>
        <p class="text-white/60 text-sm mt-3">{{ $t('organization.invite.loading', 'Loading invitation...') }}</p>
      </div>

      <!-- Invalid / expired / error -->
      <div v-else-if="error" class="py-4">
        <h1 class="text-white text-lg font-semibold mb-2">{{ $t('organization.invite.invalidTitle', 'Invitation unavailable') }}</h1>
        <p class="text-white/60 text-sm mb-6">{{ error }}</p>
        <button
          class="px-4 py-2 rounded-lg bg-white/10 text-white text-sm hover:bg-white/15"
          @click="goHome"
        >
          {{ $t('common.goHome', 'Go to home') }}
        </button>
      </div>

      <!-- Accepted -->
      <div v-else-if="accepted" class="py-4">
        <h1 class="text-white text-lg font-semibold mb-2">{{ $t('organization.invite.acceptedTitle', "You're in!") }}</h1>
        <p class="text-white/60 text-sm mb-6">
          {{ $t('organization.invite.acceptedBody', 'You have joined the organization.') }}
        </p>
        <button
          class="px-4 py-2 rounded-lg bg-purple-500 text-white text-sm hover:bg-purple-400"
          @click="goDashboard"
        >
          {{ $t('organization.invite.continue', 'Continue') }}
        </button>
      </div>

      <!-- Preview + accept -->
      <div v-else-if="invitation" class="py-4">
        <h1 class="text-white text-lg font-semibold mb-1">
          {{ $t('organization.invite.previewTitle', "You're invited") }}
        </h1>
        <p class="text-white/60 text-sm mb-6">
          {{ $t('organization.invite.previewBody', 'Join {org} as {role}.', {
            org: invitation.organizationName || $t('organization.invite.anOrg', 'an organization'),
            role: invitation.role
          }) }}
        </p>

        <button
          v-if="isLoggedIn"
          :disabled="accepting"
          class="w-full px-4 py-2 rounded-lg bg-purple-500 text-white text-sm hover:bg-purple-400 disabled:opacity-50"
          @click="accept"
        >
          {{ accepting
            ? $t('organization.invite.accepting', 'Accepting...')
            : $t('organization.invite.accept', 'Accept invitation') }}
        </button>

        <button
          v-else
          class="w-full px-4 py-2 rounded-lg bg-purple-500 text-white text-sm hover:bg-purple-400"
          @click="goLogin"
        >
          {{ $t('organization.invite.loginToAccept', 'Log in to accept') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { organizationAPI } from '@/api/organization'
import { authAPI } from '@/api/auth'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const accepting = ref(false)
const accepted = ref(false)
const error = ref('')
const invitation = ref(null)
const isLoggedIn = ref(false)

const token = route.params.token

function goHome() { router.push('/') }
function goDashboard() { router.push('/dashboard') }

function goLogin() {
  // Preserve the invite path so the user returns here after login.
  // Login.vue consumes sessionStorage.redirectAfterLogin on success.
  try {
    sessionStorage.setItem('redirectAfterLogin', route.fullPath)
  } catch {
    // sessionStorage unavailable — fall through to plain /login.
  }
  router.push('/login')
}

async function accept() {
  accepting.value = true
  error.value = ''
  try {
    const result = await organizationAPI.acceptInvitation(token)
    if (result.ok) {
      accepted.value = true
    } else {
      error.value = result.error || 'Failed to accept invitation.'
    }
  } finally {
    accepting.value = false
  }
}

onMounted(async () => {
  isLoggedIn.value = authAPI.isLoggedIn()

  if (!token) {
    error.value = 'Missing invitation token.'
    loading.value = false
    return
  }

  const result = await organizationAPI.resolveInvitation(token)
  if (result.ok && result.invitation) {
    if (!result.invitation.valid) {
      error.value = 'This invitation is no longer valid (expired, revoked, or already used).'
    } else {
      invitation.value = result.invitation
    }
  } else {
    error.value = result.error || 'Invitation not found or invalid.'
  }
  loading.value = false
})
</script>

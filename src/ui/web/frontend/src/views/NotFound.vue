<template>
  <div class="min-h-screen bg-gray-950 flex items-center justify-center p-4 overflow-hidden relative">
    <!-- Animated Background Grid -->
    <div class="absolute inset-0 overflow-hidden">
      <div class="absolute inset-0 bg-[linear-gradient(rgba(99,102,241,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(99,102,241,0.03)_1px,transparent_1px)] bg-[size:64px_64px]"></div>
      <!-- Glowing orbs -->
      <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-gray-500/10 rounded-full blur-3xl"></div>
      <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-gray-500/10 rounded-full blur-3xl"></div>
    </div>

    <!-- Content -->
    <div class="relative z-10 max-w-lg w-full">
      <!-- 404 Animation Container -->
      <div class="text-center mb-8">
        <!-- Large 404 Text -->
        <div class="relative inline-flex items-center justify-center">
          <span class="text-[150px] font-bold bg-gradient-to-br from-gray-600 to-gray-800 bg-clip-text text-transparent select-none leading-none">
            404
          </span>
        </div>
      </div>

      <!-- Title -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-white mb-3">
          {{ $t('notFound.title') }}
        </h1>
        <p class="text-gray-400">{{ $t('notFound.message') }}</p>
      </div>

      <!-- Card -->
      <div class="bg-gray-900/80 backdrop-blur-xl border border-gray-800 rounded-2xl overflow-hidden">
        <!-- Info Section -->
        <div class="p-6">
          <div class="flex items-center gap-4 pb-6 border-b border-gray-800">
            <div class="relative">
              <div class="w-16 h-16 rounded-xl bg-gray-800 flex items-center justify-center">
                <FileQuestion :size="32" class="text-gray-500" />
              </div>
            </div>
            <div class="flex-1">
              <h3 class="text-lg font-semibold text-white">{{ $t('notFound.pageNotExist') }}</h3>
              <p class="text-sm text-gray-500">{{ $t('notFound.checkUrl') }}</p>
            </div>
          </div>

          <!-- Suggestions -->
          <div class="py-6 space-y-4">
            <p class="text-sm text-gray-400">{{ $t('notFound.suggestions') }}</p>
            <ul class="space-y-2 text-sm text-gray-500">
              <li class="flex items-center gap-2">
                <div class="w-1.5 h-1.5 rounded-full bg-gray-600"></div>
                {{ $t('notFound.suggestion1') }}
              </li>
              <li class="flex items-center gap-2">
                <div class="w-1.5 h-1.5 rounded-full bg-gray-600"></div>
                {{ $t('notFound.suggestion2') }}
              </li>
              <li class="flex items-center gap-2">
                <div class="w-1.5 h-1.5 rounded-full bg-gray-600"></div>
                {{ $t('notFound.suggestion3') }}
              </li>
            </ul>
          </div>
        </div>

        <!-- Actions -->
        <div class="p-6 bg-gray-900/50 border-t border-gray-800 space-y-3">
          <router-link
            to="/"
            class="group w-full flex items-center justify-center gap-2 px-6 py-3.5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-semibold rounded-xl transition-all relative overflow-hidden"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-purple-400 to-blue-400 opacity-0 group-hover:opacity-20 transition-opacity"></div>
            <Home :size="18" />
            {{ $t('notFound.goHome') }}
            <ArrowRight :size="16" class="group-hover:translate-x-1 transition-transform" />
          </router-link>

          <div class="grid grid-cols-2 gap-3">
            <button
              @click="goBack"
              class="flex items-center justify-center gap-2 px-4 py-3 bg-gray-800 hover:bg-gray-700 text-gray-300 font-medium rounded-xl transition-all border border-gray-700 hover:border-gray-600"
            >
              <ArrowLeft :size="16" />
              {{ $t('notFound.goBack') }}
            </button>

            <router-link
              to="/my-templates"
              class="flex items-center justify-center gap-2 px-4 py-3 bg-gray-800 hover:bg-gray-700 text-gray-300 font-medium rounded-xl transition-all border border-gray-700 hover:border-gray-600"
            >
              <FolderOpen :size="16" />
              {{ $t('notFound.myTemplates') }}
            </router-link>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <p class="text-center text-gray-600 text-sm mt-6">
        {{ $t('notFound.helpText') }}
        <a :href="supportEmailHref" class="text-purple-400 hover:text-purple-300 transition-colors">
          {{ $t('notFound.contactSupport') }}
        </a>
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { FileQuestion, Home, ArrowRight, ArrowLeft, FolderOpen } from 'lucide-vue-next'
import { DEFAULTS } from '@/config/defaults'

const router = useRouter()
const supportEmailHref = computed(() => `mailto:${DEFAULTS.APP.SUPPORT_EMAIL}`)

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}
</script>

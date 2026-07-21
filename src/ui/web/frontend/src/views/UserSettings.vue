<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-900 via-gray-900 to-gray-900">
    <!-- Header -->
    <header class="sticky top-0 z-20 backdrop-blur-xl bg-gray-900/80 border-b border-white/10">
      <div class="max-w-7xl mx-auto px-4 py-4">
        <div class="flex items-center gap-4">
          <button
            @click="router.back()"
            class="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-xl transition-all"
            aria-label="Go back"
          >
            <ArrowLeft :size="20" />
          </button>
          <div>
            <h1 class="text-xl font-bold text-white">{{ $t('userSettings.title') }}</h1>
            <p class="text-sm text-gray-400">{{ $t('userSettings.subtitle') }}</p>
          </div>
        </div>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center items-center h-64">
      <div class="relative">
        <div class="w-16 h-16 border-4 border-purple-500/20 rounded-full"></div>
        <div class="absolute top-0 left-0 w-16 h-16 border-4 border-transparent border-t-purple-500 rounded-full animate-spin"></div>
      </div>
    </div>

    <!-- Main Layout -->
    <div v-else class="max-w-7xl mx-auto px-4 py-8">
      <div class="flex flex-col lg:flex-row gap-8">
        <!-- Sidebar Navigation -->
        <aside class="lg:w-64 shrink-0">
          <nav class="lg:sticky lg:top-24 space-y-1 bg-gray-800/30 rounded-2xl p-3 border border-white/5">
            <button
              v-for="section in sections"
              :key="section.id"
              @click="activeSection = section.id"
              :class="[
                'w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all',
                activeSection === section.id
                  ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-white border border-purple-500/30'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              ]"
            >
              <component :is="section.icon" :size="20" :class="activeSection === section.id ? 'text-purple-400' : ''" />
              <span class="font-medium">{{ section.label }}</span>
            </button>
          </nav>
        </aside>

        <!-- Main Content -->
        <main class="flex-1 min-w-0">
          <div class="space-y-6">
            <!-- Profile Section -->
            <section v-show="activeSection === 'profile'" class="space-y-6">
              <!-- Avatar Card -->
              <div class="bg-gray-800/40 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden">
                <!-- Cover gradient -->
                <div class="h-24 bg-gradient-to-r from-purple-600/40 via-pink-500/40 to-blue-500/40"></div>

                <div class="px-6 pb-6">
                  <!-- Avatar -->
                  <div class="relative -mt-12 mb-4">
                    <div class="relative inline-block group/avatar">
                      <img
                        v-if="form.avatarUrl"
                        :src="form.avatarUrl"
                        :alt="$t('alt.avatar')"
                        class="w-24 h-24 rounded-2xl object-cover border-4 border-gray-800 shadow-xl"
                      />
                      <div
                        v-else
                        class="w-24 h-24 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-3xl font-bold border-4 border-gray-800 shadow-xl"
                      >
                        {{ (form.displayName || 'U').charAt(0).toUpperCase() }}
                      </div>

                      <!-- Upload overlay -->
                      <label class="absolute inset-0 flex items-center justify-center bg-black/50 rounded-2xl opacity-0 group-hover/avatar:opacity-100 cursor-pointer transition-opacity">
                        <Camera :size="24" class="text-white" />
                        <input
                          ref="fileInputRef"
                          type="file"
                          accept="image/*"
                          class="hidden"
                          @change="handleFileSelect"
                        />
                      </label>

                      <!-- Remove button -->
                      <button
                        v-if="form.avatarUrl"
                        type="button"
                        @click="removeAvatar"
                        class="absolute -top-1 -right-1 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover/avatar:opacity-100 transition-opacity shadow-lg hover:bg-red-600"
                        aria-label="Remove avatar"
                      >
                        <X :size="14" />
                      </button>
                    </div>
                  </div>

                  <!-- Upload hint -->
                  <p class="text-xs text-gray-500 mb-6">{{ $t('userSettings.avatarHint') }}</p>

                  <!-- Form Fields -->
                  <div class="space-y-5">
                    <!-- Display Name -->
                    <div>
                      <label class="block text-sm font-medium text-gray-300 mb-2">
                        {{ $t('userSettings.displayName') }}
                      </label>
                      <AppInput
                        v-model="form.displayName"
                        :placeholder="$t('userSettings.displayNamePlaceholder')"
                      />
                    </div>

                    <!-- Username -->
                    <div>
                      <label class="block text-sm font-medium text-gray-300 mb-2">
                        {{ $t('userSettings.username') }}
                      </label>
                      <div class="relative">
                        <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">@</span>
                        <AppInput
                          v-model="form.username"
                          class="!pl-10"
                          :placeholder="$t('userSettings.usernamePlaceholder')"
                        />
                      </div>
                      <p class="text-xs text-gray-500 mt-1">{{ $t('userSettings.usernameHint') }}</p>
                    </div>

                    <!-- Bio -->
                    <div>
                      <label class="block text-sm font-medium text-gray-300 mb-2">
                        {{ $t('userSettings.bio') }}
                      </label>
                      <AppTextarea
                        v-model="form.bio"
                        :rows="3"
                        :placeholder="$t('userSettings.bioPlaceholder')"
                      />
                      <p class="text-xs text-gray-500 mt-1">{{ form.bio?.length || 0 }}/200</p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <!-- Account Section -->
            <section v-show="activeSection === 'account'" class="space-y-6">
              <div class="bg-gray-800/40 backdrop-blur-xl rounded-2xl border border-white/10 p-6">
                <div class="flex items-center gap-3 mb-6">
                  <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                    <Shield :size="20" class="text-white" />
                  </div>
                  <h2 class="text-lg font-semibold text-white">{{ $t('userSettings.accountInfo') }}</h2>
                </div>

                <div class="space-y-4">
                  <!-- Email -->
                  <div class="flex justify-between items-center py-4 border-b border-white/5">
                    <div>
                      <div class="text-sm text-gray-400">{{ $t('userSettings.email') }}</div>
                      <div class="text-white font-medium">{{ currentUser?.email || '-' }}</div>
                    </div>
                    <div class="flex items-center gap-2 text-emerald-400 text-sm">
                      <CheckCircle :size="16" />
                      {{ $t('userSettings.verified') }}
                    </div>
                  </div>

                  <!-- User ID -->
                  <div class="flex justify-between items-center py-4 border-b border-white/5">
                    <div>
                      <div class="text-sm text-gray-400">{{ $t('userSettings.userId') }}</div>
                      <div class="text-white font-mono text-sm">{{ currentUser?.uid || currentUser?.id || '-' }}</div>
                    </div>
                    <button
                      @click="copyUserId"
                      class="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-all"
                      :title="$t('common.copy')"
                    >
                      <Copy :size="16" />
                    </button>
                  </div>

                  <!-- Member Since -->
                  <div class="flex justify-between items-center py-4" :class="{ 'border-b border-white/5': isTrialActive || isTrialExpired }">
                    <div>
                      <div class="text-sm text-gray-400">{{ $t('userSettings.memberSince') }}</div>
                      <div class="text-white">{{ formatDate(currentUser?.createdAt) }}</div>
                    </div>
                    <Calendar :size="16" class="text-gray-500" />
                  </div>

                  <!-- Plan / Trial Status (cloud only) -->
                  <div v-if="isTrialActive || isTrialExpired" class="flex justify-between items-center py-4">
                    <div>
                      <div class="text-sm text-gray-400">{{ $t('cloudTrial.planLabel', 'Plan') }}</div>
                      <div v-if="isTrialActive" class="text-blue-400 font-medium">
                        {{ $t('cloudTrial.trialActive', 'Free Trial') }}
                        <span class="text-gray-400 font-normal">
                          — {{ $t('cloudTrial.daysRemaining', { days: trialDaysRemaining }) }}
                        </span>
                      </div>
                      <div v-else class="text-red-400 font-medium">
                        {{ $t('cloudTrial.expired') }}
                      </div>
                    </div>
                    <router-link
                      to="/pricing"
                      class="px-3 py-1.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs font-semibold rounded-lg hover:shadow-lg transition-all"
                    >
                      {{ $t('cloudTrial.upgrade') }}
                    </router-link>
                  </div>
                </div>
              </div>
            </section>

            <!-- Linked Accounts Section -->
            <section v-show="activeSection === 'linked'" class="space-y-6">
              <LinkedAccounts />
            </section>

            <!-- API Keys Section -->
            <section v-show="activeSection === 'api'" class="space-y-6">
              <MyApiKeys />
            </section>

            <!-- Licenses Section -->
            <section v-show="activeSection === 'licenses'" class="space-y-6">
              <MyLicenses />
            </section>

            <!-- AI Assistant Section -->
            <section v-show="activeSection === 'ai'" class="space-y-6">
              <AISettings />
            </section>

            <!-- Devices Section -->
            <section v-show="activeSection === 'devices'" class="space-y-6">
              <div class="bg-gray-800/40 backdrop-blur-xl rounded-2xl border border-white/10 p-6">
                <div class="flex items-center gap-3 mb-6">
                  <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-blue-500 flex items-center justify-center">
                    <MonitorSmartphone :size="20" class="text-white" />
                  </div>
                  <h2 class="text-lg font-semibold text-white">{{ $t('userSettings.myDevices', 'My Devices') }}</h2>
                </div>

                <div v-if="deviceStore.loading" class="flex justify-center py-8">
                  <Loader2 :size="24" class="animate-spin text-gray-400" />
                </div>

                <div v-else-if="deviceStore.devices.length === 0" class="text-center py-8">
                  <MonitorSmartphone :size="32" class="mx-auto text-gray-600 mb-3" />
                  <p class="text-sm text-gray-400">{{ $t('userSettings.noDevices', 'No devices registered') }}</p>
                  <p class="text-xs text-gray-500 mt-1">{{ $t('userSettings.noDevicesHint', 'Open the desktop app to auto-register your device') }}</p>
                </div>

                <div v-else class="space-y-4">
                  <div
                    v-for="device in deviceStore.devices"
                    :key="device.id"
                    class="flex items-center justify-between p-4 bg-gray-800/60 rounded-xl border border-white/5"
                  >
                    <div class="flex items-center gap-3">
                      <div
                        :class="[
                          'w-3 h-3 rounded-full',
                          device.isOnline ? 'bg-emerald-400 shadow-lg shadow-emerald-500/30' : 'bg-gray-500'
                        ]"
                      ></div>
                      <div>
                        <div class="text-white font-medium">{{ device.name || device.id.slice(0, 8) }}</div>
                        <div class="text-xs text-gray-400 flex items-center gap-2">
                          <span v-if="device.platform">{{ device.platform }}</span>
                          <span v-if="device.version">v{{ device.version }}</span>
                        </div>
                      </div>
                    </div>

                    <div class="flex items-center gap-4">
                      <!-- Remote Wake Toggle -->
                      <div class="flex items-center gap-2">
                        <span class="text-xs text-gray-400">{{ $t('userSettings.remoteWake', 'Remote Wake') }}</span>
                        <label class="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            class="sr-only peer"
                            :checked="device.remoteWakeEnabled"
                            @change="toggleDeviceRemoteWake(device)"
                          />
                          <div class="w-9 h-5 bg-gray-600 rounded-full peer peer-checked:bg-purple-500 transition-colors after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-4"></div>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>

                <p class="text-xs text-gray-500 mt-4">
                  {{ $t('userSettings.remoteWakeHint', 'When Remote Wake is enabled, you can start this device remotely from the mobile app even when the desktop app is closed.') }}
                </p>
              </div>
            </section>

            <!-- Danger Zone Section -->
            <section v-show="activeSection === 'danger'" class="space-y-6">
              <div class="bg-gray-800/40 backdrop-blur-xl rounded-2xl border border-red-500/30 p-6">
                <div class="flex items-center gap-3 mb-6">
                  <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center">
                    <AlertTriangle :size="20" class="text-white" />
                  </div>
                  <div>
                    <h2 class="text-lg font-semibold text-red-400">{{ $t('userSettings.dangerZone') }}</h2>
                    <p class="text-sm text-gray-500">{{ $t('userSettings.dangerZoneDesc') }}</p>
                  </div>
                </div>

                <div class="p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                      <h3 class="text-white font-medium">{{ $t('userSettings.deleteAccount') }}</h3>
                      <p class="text-sm text-gray-400 mt-1">{{ $t('userSettings.deleteAccountDesc') }}</p>
                    </div>
                    <button
                      @click="showDeleteConfirm = true"
                      class="px-4 py-2 bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/30 transition-colors whitespace-nowrap"
                    >
                      {{ $t('userSettings.deleteAccount') }}
                    </button>
                  </div>
                </div>
              </div>
            </section>

            <!-- Save Button (for profile section) -->
            <div v-show="activeSection === 'profile'" class="flex justify-end gap-4 pt-4">
              <button
                @click="router.back()"
                class="px-6 py-3 text-gray-300 hover:text-white hover:bg-white/10 rounded-xl transition-all"
              >
                {{ $t('common.cancel') }}
              </button>
              <button
                @click="saveProfile"
                :disabled="saving"
                class="group relative px-8 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-medium rounded-xl transition-all hover:shadow-lg hover:shadow-purple-500/30 disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden"
              >
                <div class="absolute inset-0 bg-gradient-to-r from-purple-400 to-pink-400 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <span class="relative flex items-center gap-2">
                  <Loader2 v-if="saving" :size="18" class="animate-spin" />
                  <Save v-else :size="18" />
                  {{ saving ? $t('userSettings.saving') : $t('userSettings.save') }}
                </span>
              </button>
            </div>

            <!-- Messages -->
            <div v-if="errorMessage" class="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 flex items-center gap-3">
              <AlertCircle :size="20" />
              {{ errorMessage }}
            </div>

            <div v-if="successMessage" class="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 flex items-center gap-3">
              <Check :size="20" />
              {{ successMessage }}
            </div>
          </div>
        </main>

        <!-- Profile Preview Card -->
        <aside class="lg:w-80 shrink-0">
          <div class="lg:sticky lg:top-24">
            <div class="bg-gray-800/40 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden">
              <!-- Preview Header -->
              <div class="px-4 py-3 border-b border-white/10 bg-gray-800/50">
                <div class="flex items-center gap-2 text-sm text-gray-400">
                  <Eye :size="16" />
                  {{ $t('userSettings.previewTitle') }}
                </div>
              </div>

              <!-- Preview Content -->
              <div class="p-6">
                <!-- Cover -->
                <div class="h-16 -mx-6 -mt-6 mb-4 bg-gradient-to-r from-purple-600/60 via-pink-500/60 to-blue-500/60"></div>

                <!-- Avatar & Name -->
                <div class="flex items-start gap-4 -mt-10 mb-4">
                  <img
                    v-if="form.avatarUrl"
                    :src="form.avatarUrl"
                    :alt="$t('alt.avatar')"
                    class="w-16 h-16 rounded-xl object-cover border-2 border-gray-800 shadow-lg"
                  />
                  <div
                    v-else
                    class="w-16 h-16 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white text-2xl font-bold border-2 border-gray-800 shadow-lg"
                  >
                    {{ (form.displayName || 'U').charAt(0).toUpperCase() }}
                  </div>
                </div>

                <!-- Info -->
                <div class="space-y-2">
                  <h3 class="text-lg font-bold text-white">
                    {{ form.displayName || $t('userSettings.noName') }}
                  </h3>
                  <p v-if="form.username" class="text-sm text-purple-400">@{{ form.username }}</p>
                  <p v-if="form.bio" class="text-sm text-gray-400 line-clamp-3">{{ form.bio }}</p>
                  <p v-else class="text-sm text-gray-500 italic">{{ $t('userSettings.noBio') }}</p>
                </div>

                <!-- Stats preview -->
                <div class="flex gap-6 mt-4 pt-4 border-t border-white/10">
                  <div class="text-center">
                    <div class="text-lg font-bold text-white">0</div>
                    <div class="text-xs text-gray-500">{{ $t('userSettings.templates') }}</div>
                  </div>
                  <div class="text-center">
                    <div class="text-lg font-bold text-white">0</div>
                    <div class="text-xs text-gray-500">{{ $t('userSettings.followers') }}</div>
                  </div>
                </div>

                <!-- View Profile Link -->
                <router-link
                  v-if="currentUser?.uid || currentUser?.id"
                  :to="`/creators/${currentUser?.uid || currentUser?.id}`"
                  class="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-purple-400 hover:text-white hover:bg-purple-500/20 rounded-lg transition-all"
                >
                  <ExternalLink :size="14" />
                  {{ $t('userSettings.viewPublicProfile') }}
                </router-link>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>

    <!-- Delete Account Modal -->
    <Teleport to="body">
      <div
        v-if="showDeleteConfirm"
        class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        @click.self="showDeleteConfirm = false"
      >
        <div class="bg-gray-800 rounded-2xl border border-white/10 w-full max-w-md overflow-hidden">
          <div class="p-6 border-b border-white/10">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center">
                <AlertTriangle :size="24" class="text-red-400" />
              </div>
              <div>
                <h3 class="text-lg font-semibold text-white">{{ $t('userSettings.confirmDeleteTitle') }}</h3>
                <p class="text-sm text-gray-400">{{ $t('userSettings.confirmDeleteSubtitle') }}</p>
              </div>
            </div>
          </div>

          <div class="p-6">
            <div class="space-y-4">
              <div class="p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                <ul class="space-y-2 text-sm text-gray-300">
                  <li class="flex items-start gap-2">
                    <X :size="16" class="text-red-400 mt-0.5 flex-shrink-0" />
                    {{ $t('userSettings.deleteWarning1') }}
                  </li>
                  <li class="flex items-start gap-2">
                    <X :size="16" class="text-red-400 mt-0.5 flex-shrink-0" />
                    {{ $t('userSettings.deleteWarning2') }}
                  </li>
                  <li class="flex items-start gap-2">
                    <X :size="16" class="text-red-400 mt-0.5 flex-shrink-0" />
                    {{ $t('userSettings.deleteWarning3') }}
                  </li>
                </ul>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">
                  {{ $t('userSettings.typeToConfirm') }}
                </label>
                <AppInput
                  v-model="deleteConfirmText"
                  :placeholder="deleteConfirmPhrase"
                />
                <p class="text-xs text-gray-500 mt-1">
                  {{ $t('userSettings.typeExactly') }}: <code class="text-red-400">{{ deleteConfirmPhrase }}</code>
                </p>
              </div>
            </div>
          </div>

          <div class="p-6 border-t border-white/10 flex justify-end gap-3">
            <button
              @click="showDeleteConfirm = false; deleteConfirmText = ''"
              class="px-4 py-2 text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
            >
              {{ $t('common.cancel') }}
            </button>
            <button
              @click="deleteAccount"
              :disabled="deleteConfirmText !== deleteConfirmPhrase || deleting"
              class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Loader2 v-if="deleting" :size="16" class="animate-spin" />
              <Trash2 v-else :size="16" />
              {{ deleting ? $t('userSettings.deleting') : $t('userSettings.confirmDelete') }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Image Cropper Modal -->
    <ImageCropperModal
      v-model="showCropper"
      :image-src="cropperImageSrc"
      :aspect-ratio="1"
      :output-size="256"
      @cropped="handleCropped"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useUserProfile } from '@/composables/useUserProfile'
import AppInput from '@/components/common/AppInput.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'
import ImageCropperModal from '@/components/common/ImageCropperModal.vue'
import MyLicenses from '@/components/settings/MyLicenses.vue'
import MyApiKeys from '@/components/settings/MyApiKeys.vue'
import AISettings from '@/components/settings/AISettings.vue'
import LinkedAccounts from '@/components/settings/LinkedAccounts.vue'
import { telemetry } from '@/services/telemetry'
import { useDeviceStore } from '@/stores/deviceStore'
import { useCapabilitiesStore } from '@/stores/capabilitiesStore'
import { useToast } from '@/composables/useToast'
import { post } from '@/api/client'
import { STORAGE_KEYS } from '@/api/config'
import {
  ArrowLeft,
  Camera,
  User,
  Shield,
  Copy,
  Save,
  Loader2,
  AlertCircle,
  Check,
  X,
  AlertTriangle,
  Trash2,
  Eye,
  ExternalLink,
  Key,
  FileText,
  Calendar,
  CheckCircle,
  Bot,
  Link2,
  MonitorSmartphone
} from 'lucide-vue-next'

const router = useRouter()
const { t } = useI18n()
const deviceStore = useDeviceStore()
const capabilitiesStore = useCapabilitiesStore()

// Trial (cloud only)
const isTrialActive = computed(() => capabilitiesStore.isTrialActive)
const isTrialExpired = computed(() => capabilitiesStore.isTrialExpired)
const trialDaysRemaining = computed(() => capabilitiesStore.trialDaysRemaining ?? 0)
const toast = useToast()

// Active section state
const activeSection = ref('profile')

// Sidebar sections
const sections = computed(() => [
  { id: 'profile', label: t('userSettings.profile'), icon: User },
  { id: 'account', label: t('userSettings.account'), icon: Shield },
  { id: 'linked', label: t('linkedAccounts.title', 'Connected Accounts'), icon: Link2 },
  { id: 'api', label: t('userSettings.apiKeys'), icon: Key },
  { id: 'licenses', label: t('userSettings.licenses'), icon: FileText },
  { id: 'ai', label: t('userSettings.aiAssistant', 'AI Assistant'), icon: Bot },
  { id: 'devices', label: t('userSettings.devices', 'Devices'), icon: MonitorSmartphone },
  { id: 'danger', label: t('userSettings.dangerZone'), icon: AlertTriangle }
])

// Use profile composable
const {
  loading,
  saving,
  deleting,
  errorMessage,
  successMessage,
  currentUser,
  form,
  showCropper,
  cropperImageSrc,
  showDeleteConfirm,
  deleteConfirmText,
  deleteConfirmPhrase,
  loadProfile,
  saveProfile: saveProfileBase,
  copyUserId,
  formatDate,
  handleFileSelect: handleFileSelectBase,
  handleCropped: handleCroppedBase,
  removeAvatar: removeAvatarBase,
  deleteAccount: deleteAccountBase,
  setSuccessMessage
} = useUserProfile({
  onSuccess: (action) => {
    if (action === 'saved') {
      setSuccessMessage(t('userSettings.saveSuccess'))
    }
  },
  onError: (err) => {
    // Error messages are handled internally
  },
  onLogout: () => router.push('/login')
})

// File input ref
const fileInputRef = ref(null)

// Wrapper: save profile
async function saveProfile() {
  const result = await saveProfileBase()
  if (!errorMessage.value) {
    telemetry.track('profile.update', {
      fields_updated: ['display_name', 'username', 'bio'].filter(f => form.value?.[f])
    })
  }
}

// Wrapper: handle file select from event
function handleFileSelect(event) {
  const file = event.target.files?.[0]
  if (file) {
    const success = handleFileSelectBase(file)
    if (!success) {
      errorMessage.value = t('userSettings.invalidFileType')
    }
  }
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

// Wrapper: handle cropped avatar
async function handleCropped(croppedBlob) {
  await handleCroppedBase(croppedBlob)
  telemetry.track('profile.avatar_change', { action: 'upload' })
}

// Wrapper: remove avatar
async function removeAvatar() {
  await removeAvatarBase()
  telemetry.track('profile.avatar_change', { action: 'remove' })
}

// Wrapper: delete account
async function deleteAccount() {
  telemetry.track('profile.delete_account')
  await deleteAccountBase()
}

async function toggleDeviceRemoteWake(device) {
  const newVal = !device.remoteWakeEnabled
  try {
    if (newVal) {
      // Enable: install daemon + set cloud flag (backend handles both)
      const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)
      if (!refreshToken) {
        toast.error(t('userSettings.remoteWakeFailed', 'Failed to update Remote Wake') + ' (no auth token)')
        return
      }
      const res = await post('/wake-daemon/enable', { refresh_token: refreshToken })
      if (!res.ok) {
        toast.error(res.error || t('userSettings.remoteWakeFailed', 'Failed to update Remote Wake'))
        return
      }
    } else {
      // Disable: remove daemon + clear cloud flag (backend handles both)
      const res = await post('/wake-daemon/disable')
      if (!res.ok) {
        toast.error(res.error || t('userSettings.remoteWakeFailed', 'Failed to update Remote Wake'))
        return
      }
    }
    // Sync to cloud (wake-daemon/enable already tries via proxy, but may silently fail)
    await deviceStore.setRemoteWake(device.id, newVal)
    device.remoteWakeEnabled = newVal
    toast.success(newVal ? t('userSettings.remoteWakeOn', 'Remote Wake enabled') : t('userSettings.remoteWakeOff', 'Remote Wake disabled'))
  } catch (e) {
    toast.error(t('userSettings.remoteWakeFailed', 'Failed to update Remote Wake'))
  }
}

onMounted(() => {
  loadProfile()
  deviceStore.fetchDevices()
})
</script>

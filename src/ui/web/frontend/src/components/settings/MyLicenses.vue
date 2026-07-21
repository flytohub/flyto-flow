<template>
  <div class="group relative bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6 hover:border-emerald-500/30 transition-all duration-500">
    <div class="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
    <div class="relative">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
            <Key :size="20" class="text-white" />
          </div>
          <div>
            <h2 class="text-lg font-semibold text-white">{{ $t('userSettings.myLicenses') }}</h2>
            <p class="text-sm text-gray-400">{{ $t('userSettings.myLicensesDesc') }}</p>
          </div>
        </div>
        <a
          :href="EXTERNAL_URLS.BUY_OFFLINE"
          target="_blank"
          class="flex items-center gap-2 px-4 py-2 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-lg hover:bg-emerald-500/30 transition-colors text-sm"
        >
          <Plus :size="16" />
          {{ $t('userSettings.buyLicense') }}
        </a>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-12">
        <Loader2 :size="24" class="animate-spin text-emerald-400" />
      </div>

      <!-- No Licenses -->
      <div v-else-if="licenses.length === 0" class="text-center py-12">
        <div class="w-16 h-16 rounded-2xl bg-gray-700/50 flex items-center justify-center mx-auto mb-4">
          <Key :size="32" class="text-gray-500" />
        </div>
        <p class="text-gray-400 mb-4">{{ $t('userSettings.noLicenses') }}</p>
        <p class="text-sm text-gray-500 max-w-sm mx-auto">
          {{ $t('userSettings.noLicensesDesc') }}
        </p>
      </div>

      <!-- License List -->
      <div v-else class="space-y-4">
        <div
          v-for="license in licenses"
          :key="license.licenseId"
          class="p-4 bg-gray-900/50 border border-white/10 rounded-xl hover:border-emerald-500/30 transition-all"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-3 mb-2">
                <span class="px-2.5 py-0.5 bg-emerald-500/20 text-emerald-400 text-xs font-medium rounded-full">
                  {{ $t('userSettings.proOffline') }}
                </span>
                <span
                  :class="[
                    'px-2.5 py-0.5 text-xs font-medium rounded-full',
                    isExpired(license.expiresAt)
                      ? 'bg-red-500/20 text-red-400'
                      : isExpiringSoon(license.expiresAt)
                        ? 'bg-amber-500/20 text-amber-400'
                        : 'bg-emerald-500/20 text-emerald-400'
                  ]"
                >
                  {{ isExpired(license.expiresAt) ? $t('userSettings.licenseStatus.expired') : isExpiringSoon(license.expiresAt) ? $t('userSettings.licenseStatus.expiringSoon') : $t('userSettings.licenseStatus.active') }}
                </span>
              </div>
              <div class="text-sm font-mono text-gray-400 truncate mb-2">
                {{ license.licenseId }}
              </div>
              <div class="flex items-center gap-4 text-sm text-gray-500">
                <span class="flex items-center gap-1">
                  <Calendar :size="14" />
                  {{ $t('userSettings.purchased') }}: {{ formatDate(license.purchasedAt) }}
                </span>
                <span class="flex items-center gap-1">
                  <Clock :size="14" />
                  {{ $t('userSettings.expires') }}: {{ formatDate(license.expiresAt) }}
                </span>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button
                @click="downloadLicense(license.licenseId)"
                :disabled="downloadingId === license.licenseId"
                class="p-2 text-gray-400 hover:text-emerald-400 hover:bg-emerald-500/10 rounded-lg transition-all disabled:opacity-50"
                :title="$t('userSettings.downloadLicense')"
              >
                <Loader2 v-if="downloadingId === license.licenseId" :size="18" class="animate-spin" />
                <Download v-else :size="18" />
              </button>
              <button
                @click="showDeviceModal(license)"
                class="p-2 text-gray-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-all"
                :title="$t('userSettings.manageDevices')"
              >
                <Monitor :size="18" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="errorMessage" class="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-center gap-2">
        <AlertCircle :size="16" />
        {{ errorMessage }}
      </div>
    </div>

    <!-- Device Management Modal -->
    <Teleport to="body">
      <div
        v-if="showDevices"
        class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        @click.self="showDevices = false"
      >
        <div class="bg-gray-800 rounded-2xl border border-white/10 w-full max-w-lg overflow-hidden">
          <!-- Header -->
          <div class="p-6 border-b border-white/10">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
                  <Monitor :size="20" class="text-white" />
                </div>
                <div>
                  <h3 class="text-lg font-semibold text-white">{{ $t('userSettings.deviceManagement') }}</h3>
                  <p class="text-sm text-gray-400 font-mono">{{ selectedLicense?.licenseId }}</p>
                </div>
              </div>
              <button
                @click="showDevices = false"
                aria-label="Close"
                class="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-all"
              >
                <X :size="20" />
              </button>
            </div>
          </div>

          <!-- Content -->
          <div class="p-6">
            <!-- Loading devices -->
            <div v-if="loadingDevices" class="flex items-center justify-center py-8">
              <Loader2 :size="24" class="animate-spin text-blue-400" />
            </div>

            <!-- Device list -->
            <div v-else-if="selectedLicenseDevices.length > 0" class="space-y-3">
              <div
                v-for="(device, index) in selectedLicenseDevices"
                :key="index"
                class="p-4 bg-gray-900/50 border border-white/10 rounded-xl"
              >
                <div class="flex items-center justify-between">
                  <div>
                    <div class="flex items-center gap-2 mb-1">
                      <Monitor :size="16" class="text-blue-400" />
                      <span class="text-white font-medium">{{ device.name || $t('userSettings.device', { number: index + 1 }) }}</span>
                    </div>
                    <div class="text-xs font-mono text-gray-500 truncate max-w-[250px]">
                      {{ device.fingerprint }}
                    </div>
                    <div class="text-xs text-gray-500 mt-1">
                      {{ $t('userSettings.addedAt') }}: {{ formatDate(device.addedAt) }}
                    </div>
                  </div>
                  <button
                    v-if="selectedLicenseDevices.length > 1"
                    @click="removeDevice(device.fingerprint)"
                    :disabled="removingDevice"
                    class="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all disabled:opacity-50"
                    :title="$t('userSettings.removeDevice')"
                  >
                    <Loader2 v-if="removingDevice" :size="16" class="animate-spin" />
                    <Trash2 v-else :size="16" />
                  </button>
                </div>
              </div>
            </div>

            <!-- No devices -->
            <div v-else class="text-center py-8 text-gray-400">
              {{ $t('userSettings.noDevicesRegistered') }}
            </div>

            <!-- Transfer Info -->
            <div class="mt-6 p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl">
              <div class="flex items-start gap-3">
                <AlertCircle :size="20" class="text-amber-400 flex-shrink-0 mt-0.5" />
                <div class="text-sm">
                  <p class="text-amber-200 font-medium mb-1">{{ $t('userSettings.deviceTransferLimits') }}</p>
                  <p class="text-gray-400">
                    {{ $t('userSettings.transferLimitsDesc', { count: 2 - (transfersUsed || 0) }) }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Add New Device -->
            <div class="mt-4">
              <button
                @click="showAddDevice = true"
                :disabled="(selectedLicenseDevices.length >= (selectedLicenseMaxDevices || 1))"
                class="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded-xl hover:bg-blue-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Plus :size="18" />
                {{ $t('userSettings.transferToNewDevice') }}
              </button>
              <p v-if="selectedLicenseDevices.length >= (selectedLicenseMaxDevices || 1)" class="text-xs text-gray-500 mt-2 text-center">
                {{ $t('userSettings.deviceLimitReached') }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Add Device Modal -->
    <Teleport to="body">
      <div
        v-if="showAddDevice"
        class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[60] p-4"
        @click.self="showAddDevice = false"
      >
        <div class="bg-gray-800 rounded-2xl border border-white/10 w-full max-w-md overflow-hidden">
          <div class="p-6 border-b border-white/10">
            <h3 class="text-lg font-semibold text-white">{{ $t('userSettings.transferToNewDevice') }}</h3>
            <p class="text-sm text-gray-400 mt-1">{{ $t('userSettings.enterFingerprintHint') }}</p>
          </div>
          <div class="p-6">
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-300 mb-2">{{ $t('userSettings.deviceFingerprint') }}</label>
              <AppTextarea
                v-model="newDeviceFingerprint"
                :rows="3"
                :placeholder="$t('userSettings.fingerprintPlaceholder')"
              />
              <p class="text-xs text-gray-500 mt-1">
                {{ $t('userSettings.getFingerprintHint') }}
              </p>
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-300 mb-2">{{ $t('userSettings.deviceNameLabel') }}</label>
              <AppInput
                v-model="newDeviceName"
                :placeholder="$t('userSettings.deviceNamePlaceholder')"
              />
            </div>
            <div v-if="addDeviceError" class="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
              {{ addDeviceError }}
            </div>
            <div class="flex justify-end gap-3">
              <button
                @click="showAddDevice = false; newDeviceFingerprint = ''; newDeviceName = ''; addDeviceError = ''"
                class="px-4 py-2 text-gray-300 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
              >
                {{ $t('common.cancel') }}
              </button>
              <button
                @click="addDevice"
                :disabled="addingDevice || !newDeviceFingerprint.trim()"
                class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <Loader2 v-if="addingDevice" :size="16" class="animate-spin" />
                {{ $t('userSettings.transferLicense') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { authAPI } from '@/api/auth'
import { get, post, download as downloadFile } from '@/api/client'
import { ENDPOINTS } from '@/config/api'
import { EXTERNAL_URLS } from '@/config/urls'
import { safeRedirect } from '@/utils/safeRedirect'
import {
  Key,
  Plus,
  Loader2,
  Download,
  Monitor,
  Calendar,
  Clock,
  AlertCircle,
  X,
  Trash2
} from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'

const { t } = useI18n()

// State
const loading = ref(true)
const licenses = ref([])
const errorMessage = ref('')
const downloadingId = ref(null)

// Device management state
const showDevices = ref(false)
const selectedLicense = ref(null)
const selectedLicenseDevices = ref([])
const selectedLicenseMaxDevices = ref(1)
const loadingDevices = ref(false)
const removingDevice = ref(false)
const transfersUsed = ref(0)

// Add device state
const showAddDevice = ref(false)
const newDeviceFingerprint = ref('')
const newDeviceName = ref('')
const addingDevice = ref(false)
const addDeviceError = ref('')

// Load user's licenses
async function loadLicenses() {
  loading.value = true
  errorMessage.value = ''

  try {
    const user = authAPI.getLocalUser()
    if (!user?.uid && !user?.id) {
      // User not authenticated - just show empty state, not an error
      licenses.value = []
      return
    }

    // Get licenses from Gateway API
    const result = await get(ENDPOINTS.LICENSES.LIST)
    if (result.ok) {
      licenses.value = result.licenses || []
      transfersUsed.value = result.transferCountYearly || 0
    } else {
      // API returned error - show empty state instead of error
      licenses.value = []
    }
  } catch (err) {
    // Network error or other issues - show empty state
    // Only show error for actual API failures, not missing data
    licenses.value = []
  } finally {
    loading.value = false
  }
}

// Download license file
async function downloadLicense(licenseId) {
  downloadingId.value = licenseId

  try {
    const result = await post(ENDPOINTS.LICENSES.DOWNLOAD(licenseId))

    if (result.ok && result.downloadUrl) {
      // If we get a download URL, redirect to it
      safeRedirect(result.downloadUrl)
    } else if (result.ok && result.licenseData) {
      // If we get the data directly, create a blob and download
      const blob = new Blob([result.licenseData], { type: 'application/octet-stream' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'flyto2-pro.license'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } else {
      throw new Error(result.error || 'Download failed')
    }
  } catch (err) {
    errorMessage.value = t('userSettings.failedToDownload')
  } finally {
    downloadingId.value = null
  }
}

// Show device management modal
async function showDeviceModal(license) {
  selectedLicense.value = license
  showDevices.value = true
  loadingDevices.value = true

  try {
    // Get full license details from Gateway API
    const result = await get(ENDPOINTS.LICENSES.GET(license.licenseId))
    if (result.ok) {
      selectedLicenseDevices.value = result.devices || []
      selectedLicenseMaxDevices.value = result.maxDevices || 1
    }
  } catch (err) {
    // Silently handle error
  } finally {
    loadingDevices.value = false
  }
}

// Add new device
async function addDevice() {
  if (!newDeviceFingerprint.value.trim() || addingDevice.value) return

  addingDevice.value = true
  addDeviceError.value = ''

  try {
    const result = await post(ENDPOINTS.LICENSES.TRANSFER(selectedLicense.value.licenseId), {
      newFingerprint: newDeviceFingerprint.value.trim(),
      deviceName: newDeviceName.value.trim() || undefined
    })

    if (!result.ok) {
      throw new Error(result.error || 'Transfer failed')
    }

    // Refresh device list
    await showDeviceModal(selectedLicense.value)
    showAddDevice.value = false
    newDeviceFingerprint.value = ''
    newDeviceName.value = ''
    transfersUsed.value++
  } catch (err) {
    addDeviceError.value = err.message
  } finally {
    addingDevice.value = false
  }
}

// Remove device
async function removeDevice(fingerprint) {
  if (removingDevice.value) return

  removingDevice.value = true

  try {
    const { del } = await import('@/api/client')
    const result = await del(ENDPOINTS.LICENSES.REMOVE_DEVICE(selectedLicense.value.licenseId), {
      data: { fingerprint }
    })

    if (!result.ok) {
      throw new Error(result.error || 'Remove failed')
    }

    // Refresh device list
    await showDeviceModal(selectedLicense.value)
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    removingDevice.value = false
  }
}

// Helper functions
function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}

function isExpired(dateStr) {
  if (!dateStr) return false
  return new Date(dateStr) < new Date()
}

function isExpiringSoon(dateStr) {
  if (!dateStr) return false
  const expires = new Date(dateStr)
  const now = new Date()
  const daysUntilExpiry = (expires - now) / (1000 * 60 * 60 * 24)
  return daysUntilExpiry > 0 && daysUntilExpiry <= 30
}

onMounted(() => {
  loadLicenses()
})
</script>

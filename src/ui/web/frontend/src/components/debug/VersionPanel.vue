<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 translate-x-full"
      enter-to-class="opacity-100 translate-x-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 translate-x-0"
      leave-to-class="opacity-0 translate-x-full"
    >
      <div
        v-if="isOpen"
        class="fixed top-0 right-0 h-full w-[480px] bg-gray-900 border-l border-gray-700 shadow-2xl z-40 flex flex-col"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-cyan-900/20">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-cyan-600/20 rounded-lg">
              <History :size="20" class="text-cyan-400" />
            </div>
            <div>
              <h3 class="text-lg font-semibold text-white">{{ $t('debug.versions.title') }}</h3>
              <p class="text-xs text-gray-400">{{ lockCount }} {{ $t('debug.versions.lockedModules') }}</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <!-- Compare Versions Button -->
            <button
              v-if="hasVersions && versions.length >= 2"
              @click="showDiffViewer = !showDiffViewer"
              class="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg transition-colors"
              :class="showDiffViewer
                ? 'bg-purple-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
              aria-label="Compare versions"
            >
              <GitCompare :size="14" />
              {{ $t('debug.versions.compare') }}
            </button>
            <button
              @click="$emit('close')"
              class="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
              aria-label="Close"
            >
              <X :size="20" />
            </button>
          </div>
        </div>

        <!-- Module Selector -->
        <div class="px-4 py-3 border-b border-gray-700/50">
          <label class="text-xs text-gray-400 mb-1.5 block">{{ $t('debug.versions.selectModule') }}</label>
          <AppSelect
            v-model="selectedModuleId"
            :placeholder="$t('debug.versions.chooseModule')"
            :options="modules.map(m => ({ value: m.id, label: m.name || m.id }))"
          />
        </div>

        <!-- Loading -->
        <div v-if="isLoading && !hasVersions" class="flex-1 flex items-center justify-center">
          <Loader :size="32" class="text-cyan-400 animate-spin" />
        </div>

        <!-- Version List -->
        <div v-else-if="hasVersions" class="flex-1 overflow-auto">
          <div class="px-4 py-2 bg-gray-800/50 border-b border-gray-700/50">
            <h4 class="text-sm font-medium text-gray-300">{{ $t('debug.versions.available') }}</h4>
          </div>

          <div class="divide-y divide-gray-700/50">
            <div
              v-for="version in versions"
              :key="version.version"
              @click="handleSelectVersion(version)"
              class="px-4 py-3 hover:bg-gray-800/50 cursor-pointer transition-colors"
              :class="{ 'bg-cyan-900/10': selectedVersion?.version === version.version }"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="text-sm font-mono text-white">v{{ version.version }}</span>
                  <span
                    v-if="version.version === latestVersion?.version"
                    class="px-1.5 py-0.5 text-xs bg-cyan-600/20 text-cyan-400 rounded"
                  >
                    {{ $t('debug.versions.latest') }}
                  </span>
                  <Lock
                    v-if="getLockedVersion(selectedModuleId) === version.version"
                    :size="12"
                    class="text-cyan-400"
                  />
                </div>
                <span class="text-xs text-gray-500">{{ formatDate(version.releasedAt) }}</span>
              </div>

              <!-- Changelog Preview -->
              <p
                v-if="version.changelog"
                class="text-xs text-gray-400 mt-1 line-clamp-2"
              >
                {{ version.changelog }}
              </p>

              <!-- Actions -->
              <div class="flex items-center gap-2 mt-2">
                <button
                  v-if="getLockedVersion(selectedModuleId) !== version.version"
                  @click.stop="handleLockVersion(version)"
                  class="text-xs px-2 py-1 bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 rounded transition-colors"
                  aria-label="Lock version"
                >
                  <Lock :size="10" class="inline mr-1" />
                  {{ $t('debug.versions.lock') }}
                </button>
                <button
                  v-else
                  @click.stop="handleUnlockVersion(version)"
                  class="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded transition-colors"
                  aria-label="Unlock version"
                >
                  <Unlock :size="10" class="inline mr-1" />
                  {{ $t('debug.versions.unlock') }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="selectedModuleId" class="flex-1 flex flex-col items-center justify-center text-gray-400">
          <History :size="48" class="mb-3 opacity-50" />
          <p class="text-sm">{{ $t('debug.versions.noVersions') }}</p>
        </div>

        <div v-else class="flex-1 flex flex-col items-center justify-center text-gray-400">
          <Package :size="48" class="mb-3 opacity-50" />
          <p class="text-sm">{{ $t('debug.versions.selectModulePrompt') }}</p>
        </div>

        <!-- Current Locks -->
        <div v-if="lockCount > 0" class="border-t border-gray-700 bg-gray-800/50">
          <div class="px-4 py-2 border-b border-gray-700/50">
            <h4 class="text-sm font-medium text-gray-300">{{ $t('debug.versions.currentLocks') }}</h4>
          </div>
          <div class="max-h-40 overflow-auto">
            <div
              v-for="moduleId in lockedModules"
              :key="moduleId"
              class="flex items-center justify-between px-4 py-2 hover:bg-gray-700/30"
            >
              <div class="flex items-center gap-2">
                <Lock :size="12" class="text-cyan-400" />
                <span class="text-sm text-white">{{ moduleId }}</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs font-mono text-gray-400">v{{ getLockedVersion(moduleId) }}</span>
                <button
                  @click="handleUnlockModule(moduleId)"
                  class="p-1 text-gray-500 hover:text-red-400 transition-colors"
                  aria-label="Unlock module"
                >
                  <X :size="12" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Version Constraint Input -->
        <div class="px-4 py-3 border-t border-gray-700 bg-gray-800/50">
          <label class="text-xs text-gray-400 mb-1.5 block">{{ $t('debug.versions.constraint') }}</label>
          <div class="flex gap-2">
            <AppInput
              v-model="versionConstraint"
              placeholder="^1.0.0, ~2.1.0, >=3.0.0"
              class="flex-1"
            />
            <button
              @click="handleResolveConstraint"
              :disabled="!versionConstraint || !selectedModuleId"
              class="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white text-sm rounded-lg transition-colors"
              aria-label="Resolve"
            >
              {{ $t('debug.versions.resolve') }}
            </button>
          </div>
          <p v-if="resolvedVersion" class="text-xs text-cyan-400 mt-2">
            {{ $t('debug.versions.resolvedTo') }}: v{{ resolvedVersion }}
          </p>
        </div>

        <!-- Version Diff Viewer Overlay -->
        <Transition
          enter-active-class="transition ease-out duration-200"
          enter-from-class="opacity-0"
          enter-to-class="opacity-100"
          leave-active-class="transition ease-in duration-150"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
        >
          <div v-if="showDiffViewer" class="absolute inset-0 flex flex-col bg-gray-900">
            <VersionDiffViewer
              :versions="versions"
              :current-version="getLockedVersion(selectedModuleId)"
              :get-version-data="getVersionData"
              @close="showDiffViewer = false"
            />
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import AppInput from '@/components/common/AppInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import {
  History,
  X,
  Loader,
  Lock,
  Unlock,
  Package,
  GitCompare
} from 'lucide-vue-next'
import { useVersioning } from '@/composables/debug/useVersioning'
import VersionDiffViewer from './VersionDiffViewer.vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  workflowId: {
    type: String,
    required: true
  },
  modules: {
    type: Array,
    default: () => []
  },
  initialModuleId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['close', 'version-selected', 'lock-changed'])

const { t } = useI18n()

const {
  versions,
  selectedVersion,
  workflowLocks,
  isLoading,
  latestVersion,
  lockedModules,
  lockCount,
  hasVersions,
  loadVersions,
  loadWorkflowLocks,
  setVersionLock,
  removeVersionLock,
  resolveVersion,
  getLockedVersion,
  selectVersion
} = useVersioning({
  onSuccess: (event) => {
    if (event === 'version_locked' || event === 'version_unlocked') {
      emit('lock-changed', { locks: workflowLocks.value })
    }
  }
})

const selectedModuleId = ref(props.initialModuleId || '')
const versionConstraint = ref('')
const resolvedVersion = ref(null)
const showDiffViewer = ref(false)

// Get version data for diff comparison
async function getVersionData(versionNumber) {
  const version = versions.value.find(v => v.version === versionNumber)
  if (!version) return null

  // Return version metadata - can be extended to fetch full version content
  return {
    version: version.version,
    changelog: version.changelog,
    releasedAt: version.releasedAt,
    moduleId: selectedModuleId.value,
    // Add more fields as available from the version API
    ...version
  }
}

// Load locks when panel opens
watch(() => props.isOpen, async (open) => {
  if (open && props.workflowId) {
    await loadWorkflowLocks(props.workflowId)
  }
})

// Load versions when module changes
watch(selectedModuleId, async (moduleId) => {
  if (moduleId) {
    resolvedVersion.value = null
    await loadVersions(moduleId)
  }
})

function handleSelectVersion(version) {
  selectVersion(version)
  emit('version-selected', { moduleId: selectedModuleId.value, version: version.version })
}

async function handleLockVersion(version) {
  await setVersionLock(props.workflowId, selectedModuleId.value, version.version)
}

async function handleUnlockVersion(version) {
  await removeVersionLock(props.workflowId, selectedModuleId.value)
}

async function handleUnlockModule(moduleId) {
  await removeVersionLock(props.workflowId, moduleId)
}

async function handleResolveConstraint() {
  if (!versionConstraint.value || !selectedModuleId.value) return

  const result = await resolveVersion(selectedModuleId.value, versionConstraint.value)
  if (result.ok) {
    resolvedVersion.value = result.version
  }
}

function formatDate(dateString) {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString()
}
</script>

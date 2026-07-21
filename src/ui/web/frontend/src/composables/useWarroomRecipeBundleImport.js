import { computed, ref } from 'vue'
import { useToast } from '@/composables/useToast'
import {
  importWarroomBundle,
  listPendingWarroomBundles,
  scanPendingWarroomBundles,
} from '@/api/recipeBundles'

function defaultBaseUrl() {
  if (typeof window === 'undefined') return 'http://localhost:3000'
  return window.location.origin
}

function defaultProjectSlug() {
  if (typeof window === 'undefined') return 'flyto2'
  const slug = window.location.hostname
    .replace(/[^A-Za-z0-9._-]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 80)
  return slug || 'flyto2'
}

export function useWarroomRecipeBundleImport(store) {
  const toast = useToast()
  const showDialog = ref(false)
  const projectSlug = ref(defaultProjectSlug())
  const baseUrl = ref(defaultBaseUrl())
  const sourcePath = ref('')
  const pendingBundles = ref([])
  const rejectedBundles = ref([])
  const dryRunResult = ref(null)
  const importResult = ref(null)
  const error = ref('')
  const inboxError = ref('')
  const scanning = ref(false)
  const dryRunning = ref(false)
  const importing = ref(false)

  const canImport = computed(() => Boolean(dryRunResult.value?.ok && !dryRunning.value && !importing.value))

  function openDialog() {
    showDialog.value = true
    error.value = ''
    inboxError.value = ''
    importResult.value = null
    if (!projectSlug.value) projectSlug.value = defaultProjectSlug()
    if (!baseUrl.value) baseUrl.value = defaultBaseUrl()
    void refreshPendingBundles()
  }

  function closeDialog() {
    if (dryRunning.value || importing.value) return
    showDialog.value = false
  }

  async function runDryRun() {
    error.value = ''
    importResult.value = null
    dryRunResult.value = null
    dryRunning.value = true
    try {
      const result = await importWarroomBundle({
        projectSlug: projectSlug.value.trim(),
        baseUrl: baseUrl.value.trim(),
        sourcePath: sourcePath.value,
        dryRun: true,
      })
      if (!result.ok) {
        error.value = result.error || 'Warroom dry-run failed'
        return result
      }
      dryRunResult.value = result
      return result
    } finally {
      dryRunning.value = false
    }
  }

  async function confirmImport() {
    if (!canImport.value) return null
    error.value = ''
    importing.value = true
    try {
      const result = await importWarroomBundle({
        projectSlug: projectSlug.value.trim(),
        baseUrl: baseUrl.value.trim(),
        sourcePath: sourcePath.value,
        dryRun: false,
      })
      if (!result.ok) {
        error.value = result.error || 'Warroom import failed'
        return result
      }
      importResult.value = result
      toast.success(sourcePath.value ? 'Warroom bundle approved' : 'Warroom recipes imported')
      await refreshTemplates(result)
      await refreshPendingBundles()
      return result
    } finally {
      importing.value = false
    }
  }

  async function refreshTemplates(result) {
    if (!store) return
    await Promise.all([
      store.fetchFolders?.(),
      store.fetchTemplates?.(true),
    ].filter(Boolean))

    const projectFolder = result?.folders?.find((folder) =>
      Array.isArray(folder.path)
      && folder.path.length === 2
      && folder.path[0] === 'Warroom'
      && folder.path[1] === projectSlug.value.trim()
    )
    if (projectFolder?.id) {
      store.selectFolder?.(projectFolder.id)
    }
  }

  async function refreshPendingBundles() {
    inboxError.value = ''
    const result = await listPendingWarroomBundles()
    applyInboxResult(result)
    return result
  }

  async function scanInbox() {
    inboxError.value = ''
    scanning.value = true
    try {
      const result = await scanPendingWarroomBundles()
      applyInboxResult(result)
      return result
    } finally {
      scanning.value = false
    }
  }

  function applyInboxResult(result) {
    if (!result?.ok) {
      pendingBundles.value = []
      rejectedBundles.value = result?.rejected || []
      inboxError.value = result?.error || 'Warroom inbox unavailable'
      return
    }
    pendingBundles.value = result.pending || []
    rejectedBundles.value = result.rejected || []
    if (sourcePath.value && !pendingBundles.value.some((bundle) => bundle.sourcePath === sourcePath.value)) {
      sourcePath.value = ''
    }
  }

  function selectPendingBundle(bundle) {
    sourcePath.value = bundle?.sourcePath || ''
    dryRunResult.value = null
    importResult.value = null
    error.value = ''
  }

  return {
    showDialog,
    projectSlug,
    baseUrl,
    sourcePath,
    pendingBundles,
    rejectedBundles,
    dryRunResult,
    importResult,
    error,
    inboxError,
    scanning,
    dryRunning,
    importing,
    canImport,
    openDialog,
    closeDialog,
    runDryRun,
    confirmImport,
    refreshPendingBundles,
    scanInbox,
    selectPendingBundle,
  }
}

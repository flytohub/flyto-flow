/**
 * MyTemplates Store
 * File Manager mode: left sidebar (folders) + right content (templates per folder)
 * Server-side search/sort/filter/pagination — frontend is pure rendering
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { templatesAPI } from '@/api/templates'
import { useUserStore } from '@/stores/userStore'
import {
  normalizeFoldersResponse,
  normalizeMyTemplatesResponse
} from '@/utils/dataBoundary'

function sortFolders(items) {
  return [...items].sort((a, b) => {
    const order = (a.order ?? 0) - (b.order ?? 0)
    if (order !== 0) return order
    return String(a.name || '').localeCompare(String(b.name || ''))
  })
}

function folderParentId(folder) {
  return folder?.parent_id ?? folder?.parentId ?? null
}

export const useMyTemplatesStore = defineStore('myTemplates', () => {
  // ========== State ==========

  // Folder sidebar
  const folders = ref([])
  const defaultFolderPosition = ref(0)
  const defaultFolderCount = ref(0)
  const totalCount = ref(0)

  // Selected folder (File Manager mode)
  const selectedFolderId = ref('__all__') // '__all__' | '__default__' | folder_id

  // Content area (templates for selected folder)
  const templates = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Full template list for Manage Folders dialog — ignores pagination so the
  // user can organise the entire library in one view.
  const allTemplatesFull = ref([])
  const allTemplatesFullLoading = ref(false)

  // Pagination
  const page = ref(1)
  const pageSize = ref(40)
  const totalFiltered = ref(0)
  const hasNext = ref(false)

  // Stats
  const stats = ref({
    totalCount: 0,
    publishedCount: 0,
    draftCount: 0,
  })

  // Filter/sort state
  const searchQuery = ref('')
  const sortBy = ref('updated')
  const statusFilter = ref(null)

  // Folder state (for legacy compat)
  const expandedFolders = ref(new Set())

  // ========== Getters ==========

  const allTemplates = computed(() => templates.value)
  const currentTemplates = computed(() => templates.value)

  // Sidebar folder tree with counts
  // "All Templates" is only meaningful when real folders exist — when there
  // are none, "Unfiled" already is everything, so the extra row is just noise.
  const folderList = computed(() => {
    const defaultItem = {
      id: '__default__',
      name: 'Unfiled',
      color: '#8B5CF6',
      count: defaultFolderCount.value,
      isVirtual: true,
      depth: 0,
      hasChildren: false,
      pathLabel: 'Unfiled',
    }

    const realFolders = folders.value.map(f => ({ ...f, isVirtual: false }))
    const childrenByParent = new Map()
    realFolders.forEach(folder => {
      const parentId = folderParentId(folder)
      if (!childrenByParent.has(parentId)) childrenByParent.set(parentId, [])
      childrenByParent.get(parentId).push(folder)
    })
    childrenByParent.forEach((children, parentId) => {
      childrenByParent.set(parentId, sortFolders(children))
    })

    const flattenFolder = (folder, depth = 0, parentPath = []) => {
      const path = Array.isArray(folder.path) && folder.path.length
        ? folder.path
        : [...parentPath, folder.name].filter(Boolean)
      const item = {
        ...folder,
        depth,
        hasChildren: Boolean(childrenByParent.get(folder.id)?.length),
        path,
        pathLabel: path.join(' / '),
      }
      const descendants = expandedFolders.value.has(folder.id)
        ? (childrenByParent.get(folder.id) || []).flatMap(child =>
            flattenFolder(child, depth + 1, path)
          )
        : []
      return [item, ...descendants]
    }

    const rootFolders = childrenByParent.get(null) || []
    const pos = Math.min(defaultFolderPosition.value, rootFolders.length)
    const ordered = [...rootFolders]
    ordered.splice(pos, 0, defaultItem)
    if (realFolders.length === 0) return ordered
    const allItem = {
      id: '__all__',
      name: 'All Templates',
      color: '#6366f1',
      count: totalCount.value,
      isVirtual: true,
      depth: 0,
      hasChildren: false,
      pathLabel: 'All Templates',
    }
    return [
      allItem,
      ...ordered.flatMap(folder => folder.isVirtual ? [folder] : flattenFolder(folder, 0, [])),
    ]
  })

  // ========== Actions ==========

  async function fetchTemplates(resetPage = true) {
    const userStore = useUserStore()
    if (!userStore.userId) {
      await userStore.waitForAuth()
      if (!userStore.userId) return
    }

    if (resetPage) page.value = 1
    loading.value = true
    error.value = null

    try {
      const params = {
        search: searchQuery.value || undefined,
        sortBy: sortBy.value,
        status: statusFilter.value || undefined,
        page: page.value,
        pageSize: pageSize.value,
      }

      // Folder filter
      if (selectedFolderId.value === '__all__') {
        // No folder filter — show all
      } else {
        params.folderId = selectedFolderId.value
      }

      const result = await templatesAPI.listMyTemplates(params)
      const normalized = normalizeMyTemplatesResponse(result, {
        page: page.value,
        pageSize: pageSize.value,
      })

      templates.value = normalized.templates
      totalFiltered.value = normalized.total
      hasNext.value = normalized.hasNext
      stats.value.draftCount = normalized.draftCount
      stats.value.publishedCount = normalized.publishedCount

      if (!normalized.ok) {
        error.value = normalized.error || 'Failed to load templates'
      }
      if (normalized.ok) {
        error.value = null
      } else {
        templates.value = []
      }
    } catch (err) {
      error.value = err.message || 'Failed to load templates'
    } finally {
      loading.value = false
    }
  }

  async function fetchAllTemplatesFull() {
    const userStore = useUserStore()
    if (!userStore.userId) {
      await userStore.waitForAuth()
      if (!userStore.userId) return
    }
    allTemplatesFullLoading.value = true
    try {
      const result = await templatesAPI.listMyTemplates({
        sortBy: sortBy.value,
        page: 1,
        pageSize: 500,
      })
      const normalized = normalizeMyTemplatesResponse(result, {
        page: 1,
        pageSize: 500,
      })
      if (normalized.ok) {
        allTemplatesFull.value = normalized.templates
      } else {
        allTemplatesFull.value = []
      }
    } finally {
      allTemplatesFullLoading.value = false
    }
  }

  async function fetchFolders() {
    const result = await templatesAPI.listFolders()
    const normalized = normalizeFoldersResponse(result)
    if (normalized.ok) {
      folders.value = normalized.folders
      defaultFolderPosition.value = normalized.defaultPosition
      defaultFolderCount.value = normalized.defaultCount
      totalCount.value = normalized.totalCount
      stats.value.totalCount = totalCount.value
      const parentIds = new Set(folders.value.filter(folder =>
        folders.value.some(child => folderParentId(child) === folder.id)
      ).map(folder => folder.id))
      if (parentIds.size) {
        expandedFolders.value = new Set([...expandedFolders.value, ...parentIds])
      }
      // When no real folders exist, __all__ is hidden from the sidebar,
      // so fall back to __default__ to keep the active highlight in sync.
      if (folders.value.length === 0 && selectedFolderId.value === '__all__') {
        selectedFolderId.value = '__default__'
      }
    } else {
      folders.value = []
      defaultFolderPosition.value = 0
      defaultFolderCount.value = 0
      totalCount.value = 0
      stats.value.totalCount = 0
      error.value = normalized.error || 'Failed to load folders'
    }
    return normalized
  }

  function selectFolder(folderId) {
    selectedFolderId.value = folderId
    fetchTemplates(true)
  }

  function nextPage() {
    if (hasNext.value) {
      page.value++
      fetchTemplates(false)
    }
  }

  function prevPage() {
    if (page.value > 1) {
      page.value--
      fetchTemplates(false)
    }
  }

  async function loadAll() {
    // Sequential on purpose: fetchFolders may flip selectedFolderId from
    // '__all__' to '__default__' when no real folders exist. If fetchTemplates
    // ran in parallel, it would query with a stale selectedFolderId and the
    // rendered list would disagree with the active sidebar item on first paint.
    loading.value = true
    error.value = null
    try {
      await fetchFolders()
      await fetchTemplates(true)
    } catch (err) {
      error.value = err.message || 'Failed to load'
    } finally {
      loading.value = false
    }
  }

  // ========== Template Actions ==========

  async function batchDelete(ids) {
    const result = await templatesAPI.batchDeleteTemplates(Array.from(ids))
    if (result.ok) {
      await Promise.all([fetchFolders(), fetchTemplates(false)])
    }
    return result
  }

  async function batchRemove(ids) {
    const result = await templatesAPI.batchRemoveFromLibrary(Array.from(ids))
    if (result.ok) {
      await Promise.all([fetchFolders(), fetchTemplates(false)])
    }
    return result
  }

  // ========== Folder Actions ==========

  function toggleFolder(folderId) {
    const newSet = new Set(expandedFolders.value)
    if (newSet.has(folderId)) newSet.delete(folderId)
    else newSet.add(folderId)
    expandedFolders.value = newSet
  }

  async function createFolder(data) {
    const result = await templatesAPI.createFolder(data)
    if (result.ok) await fetchFolders()
    return result
  }

  async function deleteFolder(folderId) {
    const result = await templatesAPI.deleteFolder(folderId)
    if (result.ok) {
      folders.value = folders.value.filter(f => f.id !== folderId)
      if (selectedFolderId.value === folderId) {
        selectFolder('__all__')
      }
      await fetchFolders()
    }
    return result
  }

  async function moveTemplates(templateIds, folderId) {
    const result = await templatesAPI.moveToFolder(templateIds, folderId)
    if (result.ok) {
      await Promise.all([
        fetchFolders(),
        fetchTemplates(false),
        fetchAllTemplatesFull(),
      ])
    }
    return result
  }

  // Legacy compat
  const createdTemplates = computed(() => templates.value.filter(t => t._source !== 'installed'))
  const installedTemplates = computed(() => templates.value.filter(t => t._source === 'installed'))
  function fetchCreated() { return fetchTemplates(true) }
  function fetchInstalled() { return fetchTemplates(true) }

  function reset() {
    templates.value = []
    allTemplatesFull.value = []
    allTemplatesFullLoading.value = false
    loading.value = false
    error.value = null
    stats.value = { totalCount: 0, publishedCount: 0, draftCount: 0 }
    searchQuery.value = ''
    sortBy.value = 'updated'
    statusFilter.value = null
    folders.value = []
    expandedFolders.value = new Set()
    defaultFolderPosition.value = 0
    defaultFolderCount.value = 0
    totalCount.value = 0
    selectedFolderId.value = '__all__'
    page.value = 1
    totalFiltered.value = 0
    hasNext.value = false
  }

  return {
    // State
    templates,
    createdTemplates,
    installedTemplates,
    loading,
    error,
    stats,
    allTemplatesFull,
    allTemplatesFullLoading,
    searchQuery,
    sortBy,
    statusFilter,
    // Folder state
    folders,
    expandedFolders,
    defaultFolderPosition,
    defaultFolderCount,
    totalCount,
    // File Manager state
    selectedFolderId,
    page,
    pageSize,
    totalFiltered,
    hasNext,
    // Getters
    allTemplates,
    currentTemplates,
    folderList,
    // Actions
    fetchTemplates,
    fetchAllTemplatesFull,
    fetchCreated,
    fetchInstalled,
    loadAll,
    batchDelete,
    batchRemove,
    selectFolder,
    nextPage,
    prevPage,
    // Folder actions
    fetchFolders,
    toggleFolder,
    createFolder,
    deleteFolder,
    moveTemplates,
    reset
  }
})

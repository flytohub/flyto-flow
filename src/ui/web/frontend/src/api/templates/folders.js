/**
 * Templates API - Folder Operations
 */
import { get, post, patch, del } from '@/api/client'
import { asObject, normalizeFoldersResponse } from '@/utils/dataBoundary'

function normalizeFolder(folder) {
  const safeFolder = asObject(folder)
  const parentId = safeFolder.parentId ?? safeFolder.parent_id ?? null
  return {
    ...safeFolder,
    parentId,
    parent_id: parentId,
    directCount: safeFolder.directCount ?? safeFolder.direct_count ?? 0,
    direct_count: safeFolder.direct_count ?? safeFolder.directCount ?? 0,
    hasChildren: Boolean(safeFolder.hasChildren ?? safeFolder.has_children),
    has_children: Boolean(safeFolder.has_children ?? safeFolder.hasChildren),
  }
}

export async function listFolders(tab) {
  try {
    const params = tab ? { tab } : {}
    const result = normalizeFoldersResponse(await get('/templates/folders/', { params }))
    if (!result.ok) return { ok: false, error: result.error, folders: [] }
    return {
      ok: true,
      folders: result.folders.map(normalizeFolder),
      defaultPosition: result.defaultPosition,
      defaultCount: result.defaultCount,
      totalCount: result.totalCount,
    }
  } catch (err) {
    return { ok: false, error: err.message, folders: [] }
  }
}

export async function createFolder(data) {
  try {
    const result = await post('/templates/folders/', data)
    if (!result.ok) return { ok: false, error: result.error }
    return { ok: true, folder: result.folder }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

export async function updateFolder(folderId, data) {
  try {
    const result = await patch(`/templates/folders/${folderId}`, data)
    if (!result.ok) return { ok: false, error: result.error }
    return { ok: true, folder: result.folder }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

export async function deleteFolder(folderId) {
  try {
    const result = await del(`/templates/folders/${folderId}`)
    if (!result.ok) return { ok: false, error: result.error }
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

export async function reorderFolders(folderIds, defaultPosition = 0) {
  try {
    const result = await post('/templates/folders/reorder/', {
      folder_ids: folderIds,
      default_position: defaultPosition,
    })
    if (!result.ok) return { ok: false, error: result.error }
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

export async function moveToFolder(templateIds, folderId, tab = undefined) {
  try {
    const body = { template_ids: templateIds, folder_id: folderId }
    if (tab) body.tab = tab
    const result = await post('/templates/folders/move/', body)
    if (!result.ok) return { ok: false, error: result.error }
    return { ok: true, moved: result.moved }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

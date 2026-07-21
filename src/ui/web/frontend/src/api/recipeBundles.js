import { get, post } from '@/api/client'
import { normalizeRecipeBundlesResponse } from '@/utils/dataBoundary'

export const WARROOM_BUNDLE_ID = 'flyto2-warroom-smoke'

function normalizeBundleError(error, fallback) {
  const message = String(error || '')
  if (/503|Backend unavailable|Network Error|ECONNREFUSED|Failed to fetch/i.test(message)) {
    return `${fallback}. Start the cloud API or try again after the backend is healthy.`
  }
  return message || fallback
}

export async function listPublicRecipeBundles() {
  try {
    const result = normalizeRecipeBundlesResponse(await get('/recipe-bundles/public'))
    if (!result.ok) {
      return {
        ok: false,
        bundles: [],
        error: normalizeBundleError(result.error, 'Starter pack catalog unavailable'),
      }
    }
    return result
  } catch (err) {
    return {
      ok: false,
      bundles: [],
      error: normalizeBundleError(err.message, 'Starter pack catalog unavailable'),
    }
  }
}

export async function installPublicRecipeBundle({
  bundleId = WARROOM_BUNDLE_ID,
  projectSlug,
  baseUrl,
  dryRun = false,
  target = 'private_warroom',
}) {
  try {
    const result = await post(`/recipe-bundles/${encodeURIComponent(bundleId)}/install`, {
      projectSlug,
      baseUrl,
      target,
      dryRun,
    })
    if (!result.ok) {
      return {
        ok: false,
        error: normalizeBundleError(result.error, 'Recipe bundle install failed'),
      }
    }
    return result
  } catch (err) {
    return { ok: false, error: normalizeBundleError(err.message, 'Recipe bundle install failed') }
  }
}

export async function importWarroomBundle({
  projectSlug,
  baseUrl,
  dryRun = false,
  bundleId = WARROOM_BUNDLE_ID,
  sourcePath = '',
}) {
  if (sourcePath) {
    return approvePendingWarroomBundle({
      sourcePath,
      projectSlug,
      baseUrl,
      dryRun,
    })
  }

  return installPublicRecipeBundle({
    bundleId,
    projectSlug,
    baseUrl,
    dryRun,
    target: 'private_warroom',
  })
}

export async function listPendingWarroomBundles() {
  try {
    return await get('/recipe-bundles/import-warroom/pending')
  } catch (err) {
    return {
      ok: false,
      pending: [],
      rejected: [],
      error: normalizeBundleError(err.message, 'Warroom inbox unavailable'),
    }
  }
}

export async function scanPendingWarroomBundles() {
  try {
    return await post('/recipe-bundles/import-warroom/scan')
  } catch (err) {
    return {
      ok: false,
      pending: [],
      rejected: [],
      error: normalizeBundleError(err.message, 'Warroom inbox scan failed'),
    }
  }
}

export async function approvePendingWarroomBundle({
  sourcePath,
  projectSlug,
  baseUrl,
  dryRun = false,
}) {
  try {
    const result = await post('/recipe-bundles/import-warroom/approve', {
      sourcePath,
      projectSlug,
      baseUrl,
      dryRun,
    })
    if (!result.ok) {
      return {
        ok: false,
        error: normalizeBundleError(result.error, 'Warroom bundle approval failed'),
      }
    }
    return result
  } catch (err) {
    return {
      ok: false,
      error: normalizeBundleError(err.message, 'Warroom bundle approval failed'),
    }
  }
}

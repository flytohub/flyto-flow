import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/api/client', () => ({
  get: vi.fn(),
  post: vi.fn()
}))

import { get, post } from '@/api/client'
import {
  approvePendingWarroomBundle,
  importWarroomBundle,
  installPublicRecipeBundle,
  listPublicRecipeBundles,
  listPendingWarroomBundles,
  scanPendingWarroomBundles,
  WARROOM_BUNDLE_ID
} from '@/api/recipeBundles'

describe('Recipe Bundle API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('lists public recipe bundles from the catalog endpoint', async () => {
    get.mockResolvedValue({ ok: true, bundles: [{ bundleId: WARROOM_BUNDLE_ID }] })

    const result = await listPublicRecipeBundles()

    expect(get).toHaveBeenCalledWith('/recipe-bundles/public')
    expect(result.bundles[0].bundleId).toBe(WARROOM_BUNDLE_ID)
  })

  it('normalizes public catalog backend outage errors', async () => {
    get.mockResolvedValue({ ok: false, error: 'Request failed with status code 503' })

    const result = await listPublicRecipeBundles()

    expect(result).toEqual({
      ok: false,
      bundles: [],
      error: 'Starter pack catalog unavailable. Start the cloud API or try again after the backend is healthy.',
    })
  })

  it('calls the public bundle install endpoint with dry-run payload', async () => {
    post.mockResolvedValue({ ok: true, dryRun: true, templateCount: 7 })

    const result = await importWarroomBundle({
      projectSlug: 'acme',
      baseUrl: 'https://app.flyto2.com',
      dryRun: true,
    })

    expect(post).toHaveBeenCalledWith(`/recipe-bundles/${WARROOM_BUNDLE_ID}/install`, {
      projectSlug: 'acme',
      baseUrl: 'https://app.flyto2.com',
      dryRun: true,
      target: 'private_warroom',
    })
    expect(result.templateCount).toBe(7)
  })

  it('encodes bundle ids for public install', async () => {
    post.mockResolvedValue({ ok: true })

    await installPublicRecipeBundle({
      bundleId: 'official/bundle',
      projectSlug: 'acme',
      baseUrl: 'https://app.flyto2.com',
    })

    expect(post).toHaveBeenCalledWith('/recipe-bundles/official%2Fbundle/install', {
      projectSlug: 'acme',
      baseUrl: 'https://app.flyto2.com',
      target: 'private_warroom',
      dryRun: false,
    })
  })

  it('returns a safe error object when the request fails', async () => {
    post.mockRejectedValue(new Error('network down'))

    const result = await importWarroomBundle({
      projectSlug: 'acme',
      baseUrl: 'https://app.flyto2.com',
    })

    expect(result).toEqual({ ok: false, error: 'network down' })
  })

  it('normalizes install backend outage errors', async () => {
    post.mockResolvedValue({ ok: false, error: 'Backend unavailable, please retry' })

    const result = await importWarroomBundle({
      projectSlug: 'acme',
      baseUrl: 'https://app.flyto2.com',
    })

    expect(result).toEqual({
      ok: false,
      error: 'Recipe bundle install failed. Start the cloud API or try again after the backend is healthy.',
    })
  })

  it('lists and scans signed Warroom inbox bundles', async () => {
    get.mockResolvedValue({ ok: true, pending: [{ sourcePath: '/tmp/flyto-bundle.yaml' }] })
    post.mockResolvedValue({ ok: true, pending: [] })

    const pending = await listPendingWarroomBundles()
    const scanned = await scanPendingWarroomBundles()

    expect(get).toHaveBeenCalledWith('/recipe-bundles/import-warroom/pending')
    expect(post).toHaveBeenCalledWith('/recipe-bundles/import-warroom/scan')
    expect(pending.pending[0].sourcePath).toBe('/tmp/flyto-bundle.yaml')
    expect(scanned.ok).toBe(true)
  })

  it('approves pending signed bundle when sourcePath is provided', async () => {
    post.mockResolvedValue({ ok: true, createdCount: 1 })

    const result = await importWarroomBundle({
      projectSlug: 'acme',
      baseUrl: 'https://app.flyto2.com',
      sourcePath: '/tmp/flyto-bundle.yaml',
      dryRun: true,
    })

    expect(post).toHaveBeenCalledWith('/recipe-bundles/import-warroom/approve', {
      sourcePath: '/tmp/flyto-bundle.yaml',
      projectSlug: 'acme',
      baseUrl: 'https://app.flyto2.com',
      dryRun: true,
    })
    expect(result.createdCount).toBe(1)
  })

  it('normalizes pending approval failures', async () => {
    post.mockResolvedValue({ ok: false, error: 'Request failed with status code 503' })

    const result = await approvePendingWarroomBundle({
      sourcePath: '/tmp/flyto-bundle.yaml',
      projectSlug: 'acme',
      baseUrl: 'https://app.flyto2.com',
    })

    expect(result).toEqual({
      ok: false,
      error: 'Warroom bundle approval failed. Start the cloud API or try again after the backend is healthy.',
    })
  })
})

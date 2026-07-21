import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WarroomRecipeBundleDialog from '@/components/templates/WarroomRecipeBundleDialog.vue'

function mountDialog(props = {}) {
  return mount(WarroomRecipeBundleDialog, {
    props: {
      show: true,
      projectSlug: 'acme',
      baseUrl: 'https://app.flyto2.com',
      ...props,
    },
    global: {
      stubs: {
        Teleport: true,
        Transition: false,
      },
    },
  })
}

describe('WarroomRecipeBundleDialog', () => {
  it('renders dry-run form and emits dry-run', async () => {
    const wrapper = mountDialog()

    expect(wrapper.text()).toContain('Import Warroom Recipes')
    expect(wrapper.text()).toContain('Credentials are runtime-only')
    expect(wrapper.text()).not.toContain('Import Recipes')

    await wrapper.find('form').trigger('submit.prevent')

    expect(wrapper.emitted('dry-run')).toHaveLength(1)
  })

  it('shows preview and emits import only after dry-run succeeds', async () => {
    const wrapper = mountDialog({
      dryRunResult: {
        ok: true,
        folderCount: 2,
        templateCount: 7,
        scenarioIds: ['footprint', 'authenticated-redteam'],
        folderPaths: [['Warroom'], ['Warroom', 'acme', 'Red Team']],
      },
    })

    expect(wrapper.text()).toContain('7')
    expect(wrapper.text()).toContain('Warroom / acme / Red Team')
    expect(wrapper.text()).toContain('authenticated-redteam')

    const importButton = wrapper.findAll('button').find((button) => button.text() === 'Import Recipes')
    expect(importButton).toBeTruthy()
    await importButton.trigger('click')

    expect(wrapper.emitted('import')).toHaveLength(1)
  })

  it('renders signed inbox bundles and emits scan/select events', async () => {
    const wrapper = mountDialog({
      pendingBundles: [{
        sourcePath: '/tmp/flyto-bundle.yaml',
        bundleId: 'flyto2-warroom-smoke',
        producer: 'flyto-warroom-test',
        assetCount: 1,
      }],
      rejectedBundles: [{ sourcePath: '/tmp/bad/flyto-bundle.yaml', error: 'bad signature' }],
    })

    expect(wrapper.text()).toContain('Signed inbox')
    expect(wrapper.text()).toContain('flyto2-warroom-smoke')
    expect(wrapper.text()).toContain('bad signature')

    const scanButton = wrapper.findAll('button').find((button) => button.text() === 'Scan')
    await scanButton.trigger('click')
    const pendingButton = wrapper.findAll('button').find((button) =>
      button.text().includes('flyto2-warroom-smoke')
    )
    await pendingButton.trigger('click')

    expect(wrapper.emitted('scan-inbox')).toHaveLength(1)
    expect(wrapper.emitted('select-pending')[0][0].sourcePath).toBe('/tmp/flyto-bundle.yaml')
  })

  it('labels signed pending import as approve', () => {
    const wrapper = mountDialog({
      sourcePath: '/tmp/flyto-bundle.yaml',
      dryRunResult: { ok: true, folderCount: 1, templateCount: 1 },
    })

    expect(wrapper.text()).toContain('Approve Bundle')
  })

  it('renders error and import result without undefined/null text', () => {
    const wrapper = mountDialog({
      error: 'base_url must not contain query strings',
      importResult: {
        ok: true,
        createdCount: 1,
        updatedCount: 6,
      },
    })

    const text = wrapper.text()
    expect(text).toContain('base_url must not contain query strings')
    expect(text).toContain('Imported 1 new and updated 6 existing recipe assets.')
    expect(text).not.toMatch(/\bundefined\b|\bnull\b|\bNaN\b/)
  })
})

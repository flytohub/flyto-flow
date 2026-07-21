import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import MoveToFolderDialog from '@/components/templates/MoveToFolderDialog.vue'

function mountDialog(props = {}) {
  return mount(MoveToFolderDialog, {
    props: {
      show: true,
      folders: [
        { id: 'warroom', name: 'Warroom', parent_id: null, order: 0 },
        { id: 'acme', name: 'acme', parent_id: 'warroom', order: 0 },
        { id: 'research', name: 'Research Footprint', parent_id: 'acme', order: 0 },
      ],
      ...props,
    },
    global: {
      mocks: {
        $t: (key) => key,
      },
      stubs: {
        Teleport: true,
        Transition: false,
      },
    },
  })
}

describe('MoveToFolderDialog', () => {
  it('renders third-level folders from parent_id relationships', () => {
    const wrapper = mountDialog()

    expect(wrapper.text()).toContain('Warroom')
    expect(wrapper.text()).toContain('acme')
    expect(wrapper.text()).toContain('Research Footprint')

    const research = wrapper.findAll('.move-folder-item')
      .find(button => button.text().includes('Research Footprint'))
    expect(research.attributes('title')).toBe('Warroom / acme / Research Footprint')
    expect(research.attributes('style')).toContain('--folder-depth: 2')
  })

  it('renders third-level folders from camelCased parentId relationships', () => {
    const wrapper = mountDialog({
      folders: [
        { id: 'warroom', name: 'Warroom', parentId: null, order: 0 },
        { id: 'acme', name: 'acme', parentId: 'warroom', order: 0 },
        { id: 'research', name: 'Research Footprint', parentId: 'acme', order: 0 },
      ],
    })

    const research = wrapper.findAll('.move-folder-item')
      .find(button => button.text().includes('Research Footprint'))
    expect(research.attributes('title')).toBe('Warroom / acme / Research Footprint')
    expect(research.attributes('style')).toContain('--folder-depth: 2')
  })
})

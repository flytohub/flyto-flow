import { describe, it, expect, vi } from 'vitest'

// Mock lucide-vue-next to avoid Vue component issues in unit tests
vi.mock('lucide-vue-next', () => {
  const icons = [
    'Navigation', 'Globe', 'Monitor', 'MousePointerClick', 'MousePointer', 'Keyboard',
    'Clock', 'Timer', 'Calendar', 'Camera',
    'FileText', 'File', 'Database', 'List', 'Braces', 'Image', 'FileCode', 'FilePenLine',
    'GitBranch', 'Repeat', 'ArrowRight', 'Blend',
    'Type', 'Hash', 'ChevronDown', 'SquareCheck', 'ToggleLeft', 'Edit', 'Tag',
    'Download', 'Upload', 'RefreshCw', 'Calculator', 'Settings', 'Code', 'ListFilter', 'X',
    'Cloud', 'MessageSquare', 'Bell',
    'LogIn', 'CreditCard', 'ShoppingCart', 'Briefcase',
    'Brain', 'Bot', 'Puzzle', 'Cpu', 'Users',
    'Share2',
    'CircleCheck', 'CirclePlus', 'CirclePlay', 'Info', 'Box', 'Package', 'Layers',
    'Grid3x3', 'ChartBar'
  ]
  const mocks = {}
  icons.forEach(name => {
    mocks[name] = { name }
  })
  return mocks
})

import { iconMap } from '@/utils/iconMap'

describe('iconMap', () => {
  it('is a non-empty object', () => {
    expect(typeof iconMap).toBe('object')
    expect(Object.keys(iconMap).length).toBeGreaterThan(0)
  })

  it('contains expected icon keys', () => {
    const expectedKeys = [
      'Monitor', 'Clock', 'FileText', 'Database', 'GitBranch',
      'Cloud', 'Brain', 'Bot', 'Settings', 'Code'
    ]
    expectedKeys.forEach(key => {
      expect(iconMap).toHaveProperty(key)
    })
  })

  it('maps Globe to Navigation component', () => {
    expect(iconMap.Globe).toEqual({ name: 'Navigation' })
  })
})

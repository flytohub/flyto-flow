import { beforeEach, describe, expect, it } from 'vitest'

import {
  getRuntimeConfig,
  resetRuntimeConfig,
  setRuntimeConfig
} from '@/config/runtime'

describe('runtime deployment contract', () => {
  beforeEach(() => resetRuntimeConfig())

  it('is empty until the local runtime contract is loaded', () => {
    expect(getRuntimeConfig()).toBeNull()
  })

  it('stores a defensive copy of the accountless local contract', () => {
    setRuntimeConfig({ deploymentMode: 'local_offline', accountRequired: false })
    expect(getRuntimeConfig()).toEqual({ deploymentMode: 'local_offline', accountRequired: false })
  })
})

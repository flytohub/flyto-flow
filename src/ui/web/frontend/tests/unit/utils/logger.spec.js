import { describe, it, expect, vi, beforeEach } from 'vitest'
import { logger } from '@/utils/logger'

describe('logger utilities', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('warn always logs', () => {
    const spy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    logger.warn('test warning')
    expect(spy).toHaveBeenCalledWith('[WARN]', 'test warning')
  })

  it('error always logs', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    logger.error('test error')
    expect(spy).toHaveBeenCalledWith('[ERROR]', 'test error')
  })

  it('warn passes multiple arguments', () => {
    const spy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    logger.warn('msg', { data: 1 }, 42)
    expect(spy).toHaveBeenCalledWith('[WARN]', 'msg', { data: 1 }, 42)
  })

  it('error passes multiple arguments', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    logger.error('msg', 'extra')
    expect(spy).toHaveBeenCalledWith('[ERROR]', 'msg', 'extra')
  })

  // In vitest, DEV is true, so debug/info/group/groupEnd/table should log
  it('debug logs in dev mode', () => {
    const spy = vi.spyOn(console, 'log').mockImplementation(() => {})
    logger.debug('debug msg')
    expect(spy).toHaveBeenCalledWith('[DEBUG]', 'debug msg')
  })

  it('info logs in dev mode', () => {
    const spy = vi.spyOn(console, 'info').mockImplementation(() => {})
    logger.info('info msg')
    expect(spy).toHaveBeenCalledWith('[INFO]', 'info msg')
  })

  it('group logs in dev mode', () => {
    const spy = vi.spyOn(console, 'group').mockImplementation(() => {})
    logger.group('test group')
    expect(spy).toHaveBeenCalledWith('test group')
  })

  it('groupEnd logs in dev mode', () => {
    const spy = vi.spyOn(console, 'groupEnd').mockImplementation(() => {})
    logger.groupEnd()
    expect(spy).toHaveBeenCalled()
  })

  it('table logs in dev mode', () => {
    const spy = vi.spyOn(console, 'table').mockImplementation(() => {})
    logger.table([{ a: 1 }])
    expect(spy).toHaveBeenCalledWith([{ a: 1 }])
  })
})

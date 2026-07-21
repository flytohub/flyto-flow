import { describe, it, expect } from 'vitest'
import { extractVariables } from '@/utils/promptTemplate'

describe('promptTemplate utilities', () => {
  describe('extractVariables', () => {
    it('extracts variables from template string', () => {
      expect(extractVariables('Hello {{name}}, your score is {{score}}'))
        .toEqual(['name', 'score'])
    })

    it('returns empty array for null/undefined/empty', () => {
      expect(extractVariables(null)).toEqual([])
      expect(extractVariables(undefined)).toEqual([])
      expect(extractVariables('')).toEqual([])
    })

    it('returns empty array for non-string input', () => {
      expect(extractVariables(42)).toEqual([])
      expect(extractVariables({})).toEqual([])
    })

    it('returns empty array when no variables present', () => {
      expect(extractVariables('Hello world')).toEqual([])
    })

    it('deduplicates variable names', () => {
      expect(extractVariables('{{name}} and {{name}} again'))
        .toEqual(['name'])
    })

    it('trims whitespace from variable names', () => {
      expect(extractVariables('{{ name }} and {{ score }}'))
        .toEqual(['name', 'score'])
    })

    it('handles single variable', () => {
      expect(extractVariables('{{url}}')).toEqual(['url'])
    })

    it('handles adjacent variables', () => {
      expect(extractVariables('{{a}}{{b}}{{c}}'))
        .toEqual(['a', 'b', 'c'])
    })

    it('ignores empty braces', () => {
      expect(extractVariables('{{}}').length).toBe(0)
    })
  })
})

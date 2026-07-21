import { describe, it, expect } from 'vitest'
import {
  createResult,
  validateGridSum,
  validateGridValues,
  validateGrid,
  validateComponentRequired,
  validateSelectOptions,
  validateRadioOptions,
  validateSection,
  validateTemplateName,
  validateTemplateId,
  validateTemplateData,
  validateWorkflowStep,
  validateFieldValue,
  validateEmail,
  validateURL,
  validateNumberRange
} from '@/utils/templateBuilder/validators'

describe('templateBuilder validators', () => {
  describe('createResult', () => {
    it('creates valid result', () => {
      expect(createResult(true)).toEqual({ valid: true, errorKey: null, params: {} })
    })

    it('creates invalid result with errorKey', () => {
      expect(createResult(false, 'error.key', { min: 5 }))
        .toEqual({ valid: false, errorKey: 'error.key', params: { min: 5 } })
    })
  })

  // -- Field Validators --

  describe('validateFieldValue', () => {
    it('returns valid when not required', () => {
      expect(validateFieldValue(null, false).valid).toBe(true)
      expect(validateFieldValue('', false).valid).toBe(true)
    })

    it('returns invalid for null/undefined when required', () => {
      expect(validateFieldValue(null, true).valid).toBe(false)
      expect(validateFieldValue(undefined, true).valid).toBe(false)
    })

    it('returns invalid for empty string when required', () => {
      expect(validateFieldValue('', true).valid).toBe(false)
      expect(validateFieldValue('   ', true).valid).toBe(false)
    })

    it('returns invalid for empty array when required', () => {
      expect(validateFieldValue([], true).valid).toBe(false)
    })

    it('returns valid for non-empty values when required', () => {
      expect(validateFieldValue('hello', true).valid).toBe(true)
      expect(validateFieldValue(42, true).valid).toBe(true)
      expect(validateFieldValue([1], true).valid).toBe(true)
    })
  })

  describe('validateEmail', () => {
    it('returns invalid for empty/null', () => {
      expect(validateEmail(null).valid).toBe(false)
      expect(validateEmail('').valid).toBe(false)
      expect(validateEmail(undefined).valid).toBe(false)
    })

    it('returns invalid for bad format', () => {
      expect(validateEmail('notanemail').valid).toBe(false)
      expect(validateEmail('missing@domain').valid).toBe(false)
      expect(validateEmail('@flyto2.com').valid).toBe(false)
    })

    it('returns valid for proper email', () => {
      expect(validateEmail('test@flyto2.com').valid).toBe(true)
      expect(validateEmail('user+tag@flyto2.com').valid).toBe(true)
    })
  })

  describe('validateURL', () => {
    it('returns invalid for empty/null', () => {
      expect(validateURL(null).valid).toBe(false)
      expect(validateURL('').valid).toBe(false)
    })

    it('returns invalid for bad URL', () => {
      expect(validateURL('not a url').valid).toBe(false)
      expect(validateURL('ftp missing scheme').valid).toBe(false)
    })

    it('returns valid for proper URL', () => {
      expect(validateURL('https://example.com').valid).toBe(true)
      expect(validateURL('http://localhost:3000').valid).toBe(true)
      expect(validateURL('ftp://files.example.com').valid).toBe(true)
    })
  })

  describe('validateNumberRange', () => {
    it('returns invalid for NaN', () => {
      expect(validateNumberRange('abc').valid).toBe(false)
    })

    it('returns invalid for below min', () => {
      const result = validateNumberRange(-5, 0, 100)
      expect(result.valid).toBe(false)
      expect(result.errorKey).toContain('tooSmall')
    })

    it('returns invalid for above max', () => {
      const result = validateNumberRange(200, 0, 100)
      expect(result.valid).toBe(false)
      expect(result.errorKey).toContain('tooLarge')
    })

    it('returns valid for in-range', () => {
      expect(validateNumberRange(50, 0, 100).valid).toBe(true)
      expect(validateNumberRange(0, 0, 100).valid).toBe(true)
      expect(validateNumberRange(100, 0, 100).valid).toBe(true)
    })

    it('handles default min/max (Infinity)', () => {
      expect(validateNumberRange(999999).valid).toBe(true)
      expect(validateNumberRange(-999999).valid).toBe(true)
    })
  })

  // -- Grid Validators --

  describe('validateGridSum', () => {
    it('returns invalid for non-array', () => {
      expect(validateGridSum(null).valid).toBe(false)
      expect(validateGridSum('not array').valid).toBe(false)
    })

    it('returns invalid for empty array', () => {
      expect(validateGridSum([]).valid).toBe(false)
    })

    it('returns invalid when sum is not 12', () => {
      const result = validateGridSum([6, 4])
      expect(result.valid).toBe(false)
      expect(result.sum).toBe(10)
    })

    it('returns valid when sum is 12', () => {
      expect(validateGridSum([12]).valid).toBe(true)
      expect(validateGridSum([6, 6]).valid).toBe(true)
      expect(validateGridSum([4, 4, 4]).valid).toBe(true)
    })
  })

  describe('validateGridValues', () => {
    it('returns invalid for non-array', () => {
      expect(validateGridValues(null).valid).toBe(false)
    })

    it('returns invalid for NaN values', () => {
      expect(validateGridValues(['abc']).valid).toBe(false)
    })

    it('returns invalid for values < 1', () => {
      expect(validateGridValues([0]).valid).toBe(false)
    })

    it('returns invalid for values > 12', () => {
      expect(validateGridValues([13]).valid).toBe(false)
    })

    it('returns valid for values 1-12', () => {
      expect(validateGridValues([6, 6]).valid).toBe(true)
      expect(validateGridValues([1, 11]).valid).toBe(true)
    })
  })

  describe('validateGrid', () => {
    it('validates values first then sum', () => {
      // Invalid value
      expect(validateGrid([0, 12]).valid).toBe(false)
      // Valid values but bad sum
      expect(validateGrid([6, 4]).valid).toBe(false)
      // All valid
      expect(validateGrid([6, 6]).valid).toBe(true)
    })
  })

  // -- Component Validators --

  describe('validateComponentRequired', () => {
    it('returns invalid for null', () => {
      expect(validateComponentRequired(null).valid).toBe(false)
    })

    it('returns invalid for missing type', () => {
      expect(validateComponentRequired({ id: 'x', label: 'x' }).valid).toBe(false)
    })

    it('returns invalid for missing id', () => {
      expect(validateComponentRequired({ type: 'text', label: 'x' }).valid).toBe(false)
    })

    it('returns invalid for missing label', () => {
      expect(validateComponentRequired({ type: 'text', id: 'x' }).valid).toBe(false)
      expect(validateComponentRequired({ type: 'text', id: 'x', label: '' }).valid).toBe(false)
      expect(validateComponentRequired({ type: 'text', id: 'x', label: '  ' }).valid).toBe(false)
    })

    it('returns valid for complete component', () => {
      expect(validateComponentRequired({ type: 'text', id: 'name', label: 'Name' }).valid).toBe(true)
    })
  })

  describe('validateSelectOptions', () => {
    it('returns invalid for non-array', () => {
      expect(validateSelectOptions(null).valid).toBe(false)
    })

    it('returns invalid for empty array', () => {
      expect(validateSelectOptions([]).valid).toBe(false)
    })

    it('returns invalid for option with empty label', () => {
      expect(validateSelectOptions([{ label: '', value: 'x' }]).valid).toBe(false)
    })

    it('returns invalid for option with no value', () => {
      expect(validateSelectOptions([{ label: 'x', value: '' }]).valid).toBe(false)
    })

    it('returns valid for proper options', () => {
      expect(validateSelectOptions([
        { label: 'A', value: 'a' },
        { label: 'B', value: 'b' }
      ]).valid).toBe(true)
    })
  })

  describe('validateRadioOptions', () => {
    it('delegates to validateSelectOptions', () => {
      expect(validateRadioOptions([]).valid).toBe(false)
      expect(validateRadioOptions([{ label: 'A', value: 'a' }]).valid).toBe(true)
    })
  })

  describe('validateSection', () => {
    it('returns invalid for null', () => {
      expect(validateSection(null).valid).toBe(false)
    })

    it('returns invalid for missing id', () => {
      expect(validateSection({ columns: 1, grid: [12], columnsData: [{}] }).valid).toBe(false)
    })

    it('returns invalid for missing columns', () => {
      expect(validateSection({ id: 's1', columns: 0, grid: [12], columnsData: [] }).valid).toBe(false)
    })

    it('returns invalid for non-array grid', () => {
      expect(validateSection({ id: 's1', columns: 1, grid: 'bad', columnsData: [{}] }).valid).toBe(false)
    })

    it('returns invalid for non-array columnsData', () => {
      expect(validateSection({ id: 's1', columns: 1, grid: [12], columnsData: 'bad' }).valid).toBe(false)
    })

    it('returns invalid for columnsData length mismatch', () => {
      expect(validateSection({
        id: 's1', columns: 2, grid: [6, 6], columnsData: [{}]
      }).valid).toBe(false)
    })

    it('returns valid for proper section', () => {
      expect(validateSection({
        id: 's1', columns: 1, grid: [12], columnsData: [{ components: [] }]
      }).valid).toBe(true)
    })
  })

  // -- Template Validators --

  describe('validateTemplateName', () => {
    it('returns invalid for empty/null', () => {
      expect(validateTemplateName(null).valid).toBe(false)
      expect(validateTemplateName('').valid).toBe(false)
      expect(validateTemplateName('   ').valid).toBe(false)
    })

    it('returns invalid for too long name', () => {
      expect(validateTemplateName('a'.repeat(101)).valid).toBe(false)
    })

    it('returns valid for proper name', () => {
      expect(validateTemplateName('My Template').valid).toBe(true)
    })
  })

  describe('validateTemplateId', () => {
    it('returns invalid for empty/null', () => {
      expect(validateTemplateId(null).valid).toBe(false)
      expect(validateTemplateId('').valid).toBe(false)
    })

    it('returns invalid for special characters', () => {
      expect(validateTemplateId('has space').valid).toBe(false)
      expect(validateTemplateId('has@char').valid).toBe(false)
    })

    it('returns invalid for too long ID', () => {
      expect(validateTemplateId('a'.repeat(51)).valid).toBe(false)
    })

    it('returns valid for alphanumeric with hyphens/underscores', () => {
      expect(validateTemplateId('my-template_01').valid).toBe(true)
    })
  })

  describe('validateTemplateData', () => {
    it('returns invalid for null', () => {
      expect(validateTemplateData(null).valid).toBe(false)
    })

    it('returns invalid for missing name', () => {
      expect(validateTemplateData({ template_id: 'abc' }).valid).toBe(false)
    })

    it('returns invalid for missing template_id', () => {
      expect(validateTemplateData({ name: 'Test' }).valid).toBe(false)
    })

    it('returns invalid for missing ui', () => {
      expect(validateTemplateData({ name: 'Test', template_id: 'test' }).valid).toBe(false)
    })

    it('returns invalid for non-array sections', () => {
      expect(validateTemplateData({
        name: 'Test', template_id: 'test', ui: { sections: 'bad' }
      }).valid).toBe(false)
    })

    it('returns valid for complete template', () => {
      expect(validateTemplateData({
        name: 'Test',
        template_id: 'test',
        ui: {
          sections: [{
            id: 's1', columns: 1, grid: [12], columnsData: [{ components: [] }]
          }]
        }
      }).valid).toBe(true)
    })
  })

  describe('validateWorkflowStep', () => {
    it('returns invalid for null', () => {
      expect(validateWorkflowStep(null).valid).toBe(false)
    })

    it('returns invalid for missing id', () => {
      expect(validateWorkflowStep({ module: 'x', params: {} }).valid).toBe(false)
    })

    it('returns invalid for missing module', () => {
      expect(validateWorkflowStep({ id: 'x', params: {} }).valid).toBe(false)
    })

    it('returns invalid for missing/invalid params', () => {
      expect(validateWorkflowStep({ id: 'x', module: 'm' }).valid).toBe(false)
      expect(validateWorkflowStep({ id: 'x', module: 'm', params: 'bad' }).valid).toBe(false)
    })

    it('returns valid for complete step', () => {
      expect(validateWorkflowStep({ id: 'step1', module: 'browser.click', params: { url: 'x' } }).valid).toBe(true)
    })
  })
})

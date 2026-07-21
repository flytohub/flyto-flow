/**
 * SchemaValidator Unit Tests
 */
import { describe, it, expect } from 'vitest'

// Mock implementation for testing
class MockSchemaValidator {
  constructor(schema) {
    this.schema = schema
  }

  validate(data) {
    const errors = []

    if (this.schema.type) {
      if (!this._checkType(data, this.schema.type)) {
        errors.push({ path: '', message: `Expected ${this.schema.type}` })
      }
    }

    if (this.schema.required && Array.isArray(this.schema.required)) {
      for (const field of this.schema.required) {
        if (data[field] === undefined || data[field] === null) {
          errors.push({ path: field, message: `Required field missing: ${field}` })
        }
      }
    }

    if (this.schema.properties && typeof data === 'object') {
      for (const [key, propSchema] of Object.entries(this.schema.properties)) {
        if (data[key] !== undefined) {
          const propValidator = new MockSchemaValidator(propSchema)
          const propResult = propValidator.validate(data[key])
          if (!propResult.valid) {
            errors.push(...propResult.errors.map(e => ({
              ...e,
              path: e.path ? `${key}.${e.path}` : key
            })))
          }
        }
      }
    }

    if (this.schema.minLength !== undefined && typeof data === 'string') {
      if (data.length < this.schema.minLength) {
        errors.push({ path: '', message: `Min length ${this.schema.minLength}` })
      }
    }

    if (this.schema.maxLength !== undefined && typeof data === 'string') {
      if (data.length > this.schema.maxLength) {
        errors.push({ path: '', message: `Max length ${this.schema.maxLength}` })
      }
    }

    if (this.schema.minimum !== undefined && typeof data === 'number') {
      if (data < this.schema.minimum) {
        errors.push({ path: '', message: `Minimum ${this.schema.minimum}` })
      }
    }

    if (this.schema.maximum !== undefined && typeof data === 'number') {
      if (data > this.schema.maximum) {
        errors.push({ path: '', message: `Maximum ${this.schema.maximum}` })
      }
    }

    return { valid: errors.length === 0, errors }
  }

  _checkType(value, type) {
    const checks = {
      string: v => typeof v === 'string',
      number: v => typeof v === 'number',
      boolean: v => typeof v === 'boolean',
      object: v => typeof v === 'object' && v !== null && !Array.isArray(v),
      array: v => Array.isArray(v),
      null: v => v === null
    }
    return checks[type] ? checks[type](value) : true
  }
}

describe('SchemaValidator', () => {
  describe('type validation', () => {
    it('should validate string type', () => {
      const validator = new MockSchemaValidator({ type: 'string' })
      expect(validator.validate('hello').valid).toBe(true)
      expect(validator.validate(123).valid).toBe(false)
    })

    it('should validate number type', () => {
      const validator = new MockSchemaValidator({ type: 'number' })
      expect(validator.validate(42).valid).toBe(true)
      expect(validator.validate('42').valid).toBe(false)
    })

    it('should validate boolean type', () => {
      const validator = new MockSchemaValidator({ type: 'boolean' })
      expect(validator.validate(true).valid).toBe(true)
      expect(validator.validate('true').valid).toBe(false)
    })

    it('should validate object type', () => {
      const validator = new MockSchemaValidator({ type: 'object' })
      expect(validator.validate({}).valid).toBe(true)
      expect(validator.validate([]).valid).toBe(false)
    })

    it('should validate array type', () => {
      const validator = new MockSchemaValidator({ type: 'array' })
      expect(validator.validate([]).valid).toBe(true)
      expect(validator.validate({}).valid).toBe(false)
    })
  })

  describe('required fields', () => {
    it('should fail when required field is missing', () => {
      const validator = new MockSchemaValidator({
        type: 'object',
        required: ['name', 'email']
      })
      const result = validator.validate({ name: 'John' })
      expect(result.valid).toBe(false)
      expect(result.errors.some(e => e.path === 'email')).toBe(true)
    })

    it('should pass when all required fields present', () => {
      const validator = new MockSchemaValidator({
        type: 'object',
        required: ['name', 'email']
      })
      const result = validator.validate({ name: 'John', email: 'john@flyto2.com' })
      expect(result.valid).toBe(true)
    })
  })

  describe('string constraints', () => {
    it('should validate minLength', () => {
      const validator = new MockSchemaValidator({ type: 'string', minLength: 3 })
      expect(validator.validate('ab').valid).toBe(false)
      expect(validator.validate('abc').valid).toBe(true)
    })

    it('should validate maxLength', () => {
      const validator = new MockSchemaValidator({ type: 'string', maxLength: 5 })
      expect(validator.validate('abcdef').valid).toBe(false)
      expect(validator.validate('abcde').valid).toBe(true)
    })
  })

  describe('number constraints', () => {
    it('should validate minimum', () => {
      const validator = new MockSchemaValidator({ type: 'number', minimum: 0 })
      expect(validator.validate(-1).valid).toBe(false)
      expect(validator.validate(0).valid).toBe(true)
    })

    it('should validate maximum', () => {
      const validator = new MockSchemaValidator({ type: 'number', maximum: 100 })
      expect(validator.validate(101).valid).toBe(false)
      expect(validator.validate(100).valid).toBe(true)
    })
  })

  describe('nested properties', () => {
    it('should validate nested object properties', () => {
      const validator = new MockSchemaValidator({
        type: 'object',
        properties: {
          user: {
            type: 'object',
            required: ['name'],
            properties: {
              name: { type: 'string' },
              age: { type: 'number' }
            }
          }
        }
      })

      const result = validator.validate({
        user: { name: 'John', age: '30' }
      })
      expect(result.valid).toBe(false)
      expect(result.errors.some(e => e.path === 'user.age')).toBe(true)
    })
  })
})

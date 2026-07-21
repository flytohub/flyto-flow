/**
 * Workflow YAML Utilities
 * Handles conversion between JSON and YAML formats
 */

/**
 * Convert workflow to YAML string
 * @param {Object} workflow - Core workflow format
 * @returns {string} YAML string
 */
export function workflowToYaml(workflow) {
  return jsonToYaml(workflow)
}

/**
 * Parse YAML string to workflow object
 * @param {string} yamlContent - YAML string
 * @returns {Object} Workflow object
 */
export function yamlToWorkflow(yamlContent) {
  return parseYaml(yamlContent)
}

/**
 * Convert JSON object to YAML string
 * @param {Object} obj - Object to convert
 * @param {number} indent - Current indentation level
 * @returns {string} YAML string
 */
export function jsonToYaml(obj, indent = 0) {
  const spaces = '  '.repeat(indent)
  let yaml = ''

  if (Array.isArray(obj)) {
    obj.forEach(item => {
      if (typeof item === 'object' && item !== null) {
        yaml += `${spaces}-\n${jsonToYaml(item, indent + 1)}`
      } else {
        yaml += `${spaces}- ${formatYamlValue(item)}\n`
      }
    })
  } else if (typeof obj === 'object' && obj !== null) {
    Object.entries(obj).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        yaml += `${spaces}${key}:\n${jsonToYaml(value, indent + 1)}`
      } else if (typeof value === 'object' && value !== null) {
        yaml += `${spaces}${key}:\n${jsonToYaml(value, indent + 1)}`
      } else {
        yaml += `${spaces}${key}: ${formatYamlValue(value)}\n`
      }
    })
  }

  return yaml
}

/**
 * Format value for YAML output
 * @param {*} value - Value to format
 * @returns {string} Formatted YAML value
 */
export function formatYamlValue(value) {
  if (value === null || value === undefined) return 'null'
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  if (typeof value === 'number') return String(value)
  if (typeof value === 'string') {
    // Quote strings with special characters
    if (value.includes(':') || value.includes('#') || value.includes('\n') ||
        value.includes('"') || value.includes("'") || value === '' ||
        value.startsWith('${') || value.includes(' #')) {
      return `"${value.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`
    }
    return value
  }
  return String(value)
}

/**
 * Simple YAML parser
 * @param {string} content - YAML string to parse
 * @returns {Object} Parsed object
 */
export function parseYaml(content) {
  const lines = content.split('\n')
  const result = {}
  const stack = [{ obj: result, indent: -1, isArray: false }]

  for (let lineIndex = 0; lineIndex < lines.length; lineIndex++) {
    const line = lines[lineIndex]
    if (!line.trim() || line.trim().startsWith('#')) continue

    const indent = line.search(/\S/)
    const trimmed = line.trim()

    // Pop stack to find parent at correct level
    while (stack.length > 1 && stack[stack.length - 1].indent >= indent) {
      stack.pop()
    }

    const parent = stack[stack.length - 1]

    if (trimmed === '-') {
      // Bare array item marker - create empty object for following properties
      const item = {}
      if (Array.isArray(parent.obj)) {
        parent.obj.push(item)
      }
      stack.push({ obj: item, indent, isArray: false })
    } else if (trimmed.startsWith('- ')) {
      // Array item with inline content
      const value = trimmed.substring(2).trim()
      const currentObj = parent.obj

      if (value.includes(':')) {
        // Object in array with inline key-value
        const item = {}
        const colonIdx = value.indexOf(':')
        const key = value.substring(0, colonIdx).trim()
        const val = value.substring(colonIdx + 1).trim()

        if (val === '' || val === '|' || val === '>') {
          // Nested object/array under this key
          const nextLine = lines[lineIndex + 1]
          if (nextLine && nextLine.trim().startsWith('-')) {
            item[key] = []
          } else {
            item[key] = {}
          }
        } else {
          item[key] = parseYamlValue(val)
        }

        if (Array.isArray(currentObj)) {
          currentObj.push(item)
        }
        stack.push({ obj: item, indent, isArray: false })
      } else {
        // Simple scalar in array
        if (Array.isArray(currentObj)) {
          currentObj.push(parseYamlValue(value))
        }
      }
    } else if (trimmed.includes(':')) {
      // Key-value pair
      const colonIdx = trimmed.indexOf(':')
      const key = trimmed.substring(0, colonIdx).trim()
      const value = trimmed.substring(colonIdx + 1).trim()

      if (value === '' || value === '|' || value === '>') {
        // Check next line to determine if array or object
        const nextLine = lines[lineIndex + 1]
        if (nextLine && nextLine.trim().startsWith('-')) {
          parent.obj[key] = []
          stack.push({ obj: parent.obj[key], indent, isArray: true })
        } else {
          parent.obj[key] = {}
          stack.push({ obj: parent.obj[key], indent, isArray: false })
        }
      } else {
        parent.obj[key] = parseYamlValue(value)
      }
    }
  }

  return result
}

/**
 * Parse YAML value to appropriate type
 * @param {string} value - String value to parse
 * @returns {*} Parsed value
 */
export function parseYamlValue(value) {
  if (value === 'null' || value === '~') return null
  if (value === 'true' || value === 'yes' || value === 'on') return true
  if (value === 'false' || value === 'no' || value === 'off') return false
  if (/^-?\d+$/.test(value)) return parseInt(value, 10)
  if (/^-?\d+\.\d+$/.test(value)) return parseFloat(value)
  if ((value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))) {
    return value.slice(1, -1)
  }
  return value
}

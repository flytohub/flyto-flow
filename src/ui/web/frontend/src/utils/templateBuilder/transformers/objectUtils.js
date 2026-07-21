/**
 * Object Utilities
 *
 * S-Grade: Common object manipulation utilities.
 * Single responsibility: Deep clone, merge, and clean objects.
 */

/**
 * Deep clone object
 * @param {any} obj - Object to clone
 * @returns {any} Cloned object
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') {
    return obj
  }

  if (obj instanceof Date) {
    return new Date(obj.getTime())
  }

  if (obj instanceof Array) {
    return obj.map(item => deepClone(item))
  }

  if (obj instanceof Object) {
    const clonedObj = {}
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key])
      }
    }
    return clonedObj
  }
}

/**
 * Clean empty and undefined values from object
 * @param {Object} obj - Object to clean
 * @param {boolean} removeEmptyStrings - Whether to remove empty strings (default: true)
 * @returns {Object} Cleaned object
 */
export function removeEmptyValues(obj, removeEmptyStrings = true) {
  if (!obj || typeof obj !== 'object') {
    return obj
  }

  const cleaned = {}

  for (const key in obj) {
    if (!obj.hasOwnProperty(key)) continue

    const value = obj[key]

    // Skip null and undefined
    if (value === null || value === undefined) continue

    // Optional: skip empty strings
    if (removeEmptyStrings && value === '') continue

    // Recursively process objects
    if (typeof value === 'object' && !Array.isArray(value)) {
      const cleanedNested = removeEmptyValues(value, removeEmptyStrings)
      if (Object.keys(cleanedNested).length > 0) {
        cleaned[key] = cleanedNested
      }
    } else {
      cleaned[key] = value
    }
  }

  return cleaned
}

/**
 * Merge default and custom properties
 * @param {Object} defaults - Default properties
 * @param {Object} custom - Custom properties
 * @returns {Object} Merged properties
 */
export function mergeProps(defaults, custom) {
  return {
    ...deepClone(defaults),
    ...deepClone(custom)
  }
}

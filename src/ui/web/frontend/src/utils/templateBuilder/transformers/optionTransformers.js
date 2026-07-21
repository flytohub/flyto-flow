/**
 * Option Transformers
 *
 * S-Grade: Option text parsing and serialization.
 * Single responsibility: Convert between option text and objects.
 */

/**
 * Convert option text to object array
 * @param {string} optionsText - Option text (one option per line, format: "label:value" or "label")
 * @returns {Array<Object>} Option object array
 */
export function parseOptionsText(optionsText) {
  if (!optionsText || typeof optionsText !== 'string') {
    return []
  }

  const lines = optionsText.trim().split('\n')
  const options = []

  lines.forEach(line => {
    const trimmedLine = line.trim()
    if (!trimmedLine) return

    // Support "label:value" or plain "label" format
    const parts = trimmedLine.split(':')

    if (parts.length >= 2) {
      // Format: "label:value"
      const label = parts[0].trim()
      const value = parts.slice(1).join(':').trim() // Handle colons in value
      if (label && value) {
        options.push({ label, value })
      }
    } else {
      // Format: "label" (value same as label)
      const label = trimmedLine
      options.push({ label, value: label })
    }
  })

  return options
}

/**
 * Convert option object array to text
 * @param {Array<Object>} options - Option object array
 * @returns {string} Option text
 */
export function stringifyOptions(options) {
  if (!Array.isArray(options)) {
    return ''
  }

  return options
    .map(option => {
      if (!option.label) return ''

      // If label and value are the same, show only label
      if (option.label === option.value) {
        return option.label
      }

      // Otherwise show "label:value"
      return `${option.label}:${option.value}`
    })
    .filter(line => line)
    .join('\n')
}

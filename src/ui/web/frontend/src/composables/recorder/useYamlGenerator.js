/**
 * YAML Generator Composable
 *
 * Generates YAML workflow from recorded browser actions.
 */

import { computed } from 'vue'

export function useYamlGenerator(recordedActions) {
  /**
   * Generate YAML workflow from actions
   */
  const generatedYaml = computed(() => {
    return generateYamlFromActions(recordedActions.value)
  })

  /**
   * Convert actions to workflow steps
   */
  function generateYamlFromActions(actions) {
    if (actions.length === 0) return '# No actions recorded'

    const steps = actions.map((action, index) => {
      let step = {}

      switch (action.type) {
        case 'navigate':
          step = {
            name: `Navigate to page`,
            module: 'browser.navigate',
            params: { url: action.value }
          }
          break
        case 'click':
          step = {
            name: `Click element`,
            module: 'browser.click',
            params: { selector: action.selector }
          }
          break
        case 'fill':
          step = {
            name: `Fill input`,
            module: 'browser.type',
            params: {
              selector: action.selector,
              text: action.value
            }
          }
          break
        case 'select':
          step = {
            name: `Select option`,
            module: 'browser.select',
            params: {
              selector: action.selector,
              value: action.value
            }
          }
          break
        case 'check':
          step = {
            name: `Toggle checkbox`,
            module: 'browser.check',
            params: { selector: action.selector }
          }
          break
        case 'hover':
          step = {
            name: `Hover element`,
            module: 'browser.hover',
            params: { selector: action.selector }
          }
          break
        case 'press':
          step = {
            name: `Press key`,
            module: 'browser.press',
            params: { key: action.value }
          }
          break
        case 'wait':
          step = {
            name: `Wait`,
            module: 'browser.wait',
            params: {
              selector: action.selector,
              timeout: parseInt(action.value) || 5000
            }
          }
          break
        case 'screenshot':
          step = {
            name: `Take screenshot`,
            module: 'browser.screenshot',
            params: { name: action.value || `screenshot_${index}` }
          }
          break
        case 'assert':
          step = {
            name: `Assert element`,
            module: 'browser.assert',
            params: {
              selector: action.selector,
              condition: action.value
            }
          }
          break
        default:
          step = {
            name: `Unknown action`,
            module: `browser.${action.type}`,
            params: action
          }
      }

      return step
    })

    // Generate YAML
    const workflow = {
      name: 'Recorded Workflow',
      description: `Recorded on ${new Date().toISOString()}`,
      version: '1.0.0',
      steps: steps
    }

    return yamlStringify(workflow)
  }

  /**
   * Simple YAML stringifier
   */
  function yamlStringify(obj, indent = 0) {
    const spaces = '  '.repeat(indent)
    let result = ''

    for (const [key, value] of Object.entries(obj)) {
      if (value === null || value === undefined) continue

      if (Array.isArray(value)) {
        result += `${spaces}${key}:\n`
        value.forEach(item => {
          if (typeof item === 'object') {
            result += `${spaces}- `
            const itemYaml = yamlStringify(item, 0).trim().split('\n')
            result += itemYaml[0] + '\n'
            itemYaml.slice(1).forEach(line => {
              result += `${spaces}  ${line}\n`
            })
          } else {
            result += `${spaces}- ${item}\n`
          }
        })
      } else if (typeof value === 'object') {
        result += `${spaces}${key}:\n${yamlStringify(value, indent + 1)}`
      } else {
        const strValue = typeof value === 'string' && value.includes(':')
          ? `"${value}"`
          : value
        result += `${spaces}${key}: ${strValue}\n`
      }
    }

    return result
  }

  /**
   * Export YAML to file
   */
  function exportYaml(showStatus) {
    const yaml = generatedYaml.value
    const blob = new Blob([yaml], { type: 'text/yaml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `recorded-workflow-${Date.now()}.yaml`
    a.click()
    URL.revokeObjectURL(url)
    if (showStatus) showStatus('YAML exported', 'success')
  }

  /**
   * Copy YAML to clipboard
   */
  async function copyYaml(showStatus) {
    try {
      await navigator.clipboard.writeText(generatedYaml.value)
      if (showStatus) showStatus('Copied to clipboard', 'success')
    } catch (error) {
      if (showStatus) showStatus('Failed to copy', 'error')
    }
  }

  return {
    generatedYaml,
    generateYamlFromActions,
    exportYaml,
    copyYaml
  }
}

/**
 * Element Suggestions composable — builds element suggestions from previous step outputs,
 * handles filtering, grouping, select mode, and item selection logic.
 * Extracted from ElementPickerField.vue
 */
import { computed } from 'vue'
import {
  MousePointerClick, Link, TextCursorInput,
  ListFilter, ChevronsUpDown, CheckSquare, ToggleRight, Circle,
} from 'lucide-vue-next'
import { useNodeOutputStore } from '@/stores/execution'

export function useElementSuggestions(props, emit) {
  const nodeOutputStore = useNodeOutputStore()

  // --- Element types & value key ---
  const elementTypes = computed(() => {
    return props.field.ui?.element_types || ['button', 'link', 'input']
  })

  const valueKey = computed(() => {
    const ui = props.field.ui
    if (!ui) return 'text'
    if (ui.value_key_from && ui.value_key_map) {
      const siblingValue = props.allParams[ui.value_key_from]
      if (siblingValue && ui.value_key_map[siblingValue]) {
        return ui.value_key_map[siblingValue]
      }
    }
    return ui.value_key || 'text'
  })

  // --- Element suggestions ---
  const suggestions = computed(() => {
    const items = []
    const types = elementTypes.value

    const steps = [...props.previousSteps].reverse()
    for (const step of steps) {
      const output = nodeOutputStore.getNodeOutput(step.id)
      if (!output || typeof output !== 'object') continue
      const hasHints = output.buttons || output.inputs || output.links || output.selects || output.checkboxes || output.radios || output.switches
      if (!hasHints) continue

      if (types.includes('button') && Array.isArray(output.buttons)) {
        const vk = valueKey.value
        for (const btn of output.buttons) {
          if (vk === 'id' && !btn.id) continue
          if (vk === 'text' && !btn.text) continue
          items.push({
            type: 'button',
            displayText: btn.text || btn.id || btn.selector,
            selector: btn.selector,
            text: btn.text || '',
            id: btn.id || '',
            source: step.id
          })
        }
      }

      if (types.includes('link') && Array.isArray(output.links)) {
        const vk = valueKey.value
        for (const link of output.links) {
          if (vk === 'id' && !link.id) continue
          if (vk === 'text' && !link.text) continue
          // Use the hint-provided selector if available; fallback to safe text selector
          const linkSelector = link.selector || `a:has-text("${(link.text || '').replace(/"/g, '\\"')}")`
          items.push({
            type: 'link',
            displayText: link.text,
            selector: linkSelector,
            text: link.text,
            id: link.id || '',
            href: link.href,
            source: step.id
          })
        }
      }

      if (types.includes('input') && Array.isArray(output.inputs)) {
        const vk = valueKey.value
        for (const input of output.inputs) {
          const hasAnyIdentifier = input.placeholder || input.name || input.id || input.label
          if (!hasAnyIdentifier) continue

          // Filter: only show inputs that have a value for the current method.
          // e.g. type_method="name" → skip inputs without a name attribute.
          if (vk === 'placeholder' && !input.placeholder) continue
          if (vk === 'name' && !input.name) continue
          if (vk === 'id' && !input.id) continue
          if (vk === 'label' && !input.label) continue

          const displayLabel = input.placeholder || input.label || input.name || input.id || input.selector
          const badgeParts = []
          if (input.type && input.type !== 'text') badgeParts.push(input.type)
          if (vk === 'selector') {
            // no extra badge needed
          } else if (input.placeholder && vk !== 'placeholder') badgeParts.push('placeholder')
          else if (input.name && vk !== 'name') badgeParts.push('name: ' + input.name)
          else if (input.id && vk !== 'id') badgeParts.push('id: ' + input.id)

          items.push({
            type: 'input',
            displayText: displayLabel,
            selector: input.selector,
            placeholder: input.placeholder || '',
            name: input.name || '',
            id: input.id || '',
            label: input.label || '',
            text: input.placeholder || input.name || '',
            inputType: input.type,
            badge: badgeParts.join(' ') || '',
            source: step.id
          })
        }
      }

      if (types.includes('checkbox') && Array.isArray(output.checkboxes)) {
        for (const cb of output.checkboxes) {
          items.push({
            type: 'checkbox',
            displayText: cb.label || cb.name || cb.id || cb.selector,
            selector: cb.selector,
            id: cb.id || '',
            name: cb.name || '',
            label: cb.label || '',
            text: cb.label || cb.name || '',
            badge: cb.checked ? 'checked' : '',
            source: step.id
          })
        }
      }

      if (types.includes('radio_option') && Array.isArray(output.radios)) {
        const selectedGroupKey = props.allParams?.selector || ''
        for (const rg of output.radios) {
          if (selectedGroupKey && rg.options?.[0]?.selector !== selectedGroupKey) {
            const matchesGroup = rg.group_key === selectedGroupKey
              || rg.options?.some(o => o.selector === selectedGroupKey)
            if (!matchesGroup) continue
          }
          for (const opt of (rg.options || [])) {
            items.push({
              type: 'radio_option',
              displayText: opt.label || opt.value,
              selector: opt.selector,
              text: opt.label || opt.value,
              value: opt.value,
              badge: rg.name || rg.group_key,
              source: step.id
            })
          }
        }
      }

      if (types.includes('radio') && Array.isArray(output.radios)) {
        for (const rg of output.radios) {
          const label = rg.name || rg.group_key || ''
          const optCount = (rg.options || []).length
          const groupSelector = rg.options?.[0]?.selector || ''
          items.push({
            type: 'radio',
            displayText: label,
            selector: groupSelector,
            text: label,
            name: rg.name || '',
            id: '',
            badge: rg.current_value || (optCount ? `${optCount} options` : ''),
            source: step.id
          })
        }
      }

      if (types.includes('switch') && Array.isArray(output.switches)) {
        for (const sw of output.switches) {
          items.push({
            type: 'switch',
            displayText: sw.label || sw.id || sw.selector,
            selector: sw.selector,
            id: sw.id || '',
            label: sw.label || '',
            text: sw.label || '',
            badge: sw.checked ? 'on' : 'off',
            source: step.id
          })
        }
      }

      const selectedSelector = props.allParams?.selector || ''

      if (types.includes('select_option') && Array.isArray(output.selects)) {
        for (const sel of output.selects) {
          if (selectedSelector && sel.selector !== selectedSelector) continue

          const selectLabel = sel.name || sel.selector
          for (const opt of (sel.options || [])) {
            if (!opt.value && !opt.label) continue
            const badgeParts = [sel.name || selectLabel]
            if (opt.selected) badgeParts.push('\u2713')
            items.push({
              type: 'select_option',
              displayText: opt.label || opt.value,
              selector: sel.selector,
              text: opt.label || opt.value,
              value: opt.value,
              option_selector: opt.option_selector || '',
              badge: badgeParts.join(' '),
              source: step.id
            })
          }
        }
      }

      if (types.includes('select') && Array.isArray(output.selects)) {
        for (const sel of output.selects) {
          const label = sel.name || sel.selector
          const optCount = (sel.options || []).length
          items.push({
            type: 'select',
            displayText: label,
            selector: sel.selector,
            text: label,
            id: '',
            name: sel.name || '',
            badge: sel.current_value || (optCount ? `${optCount} options` : (sel.lazy ? 'lazy' : '')),
            source: step.id
          })
        }
      }

      break
    }

    return items
  })

  const hasSuggestions = computed(() => suggestions.value.length > 0)

  const isSelectMode = computed(() => {
    const types = elementTypes.value
    const isOptionType = types.length === 1 && (types[0] === 'select_option' || types[0] === 'radio_option')
    return isOptionType && hasSuggestions.value
  })

  const selectedDisplayLabel = computed(() => {
    if (!props.modelValue) return ''
    const vk = valueKey.value
    for (const item of suggestions.value) {
      let itemVal
      if (vk === 'selector') itemVal = item.selector
      else if (vk === 'value') itemVal = item.value
      else if (vk === 'text') itemVal = item.text
      else if (vk === 'name') itemVal = item.name
      else if (vk === 'id') itemVal = item.id
      else if (vk === 'label') itemVal = item.label
      else itemVal = item.text || item.name || item.displayText
      if (itemVal === props.modelValue) return item.displayText
    }
    return String(props.modelValue)
  })

  const toggleTitle = computed(() => {
    if (hasSuggestions.value) {
      return `${suggestions.value.length} page elements detected`
    }
    return 'Run a snapshot step to detect page elements'
  })

  const filteredSuggestions = computed(() => {
    if (isSelectMode.value) return suggestions.value
    const query = (props.modelValue || '').toLowerCase().trim()
    if (!query) return suggestions.value
    return suggestions.value.filter(item =>
      item.displayText.toLowerCase().includes(query) ||
      item.selector.toLowerCase().includes(query)
    )
  })

  const groupedSuggestions = computed(() => {
    const groups = [
      { type: 'button', label: 'Buttons', iconComponent: MousePointerClick, items: [] },
      { type: 'link', label: 'Links', iconComponent: Link, items: [] },
      { type: 'input', label: 'Inputs', iconComponent: TextCursorInput, items: [] },
      { type: 'checkbox', label: 'Checkboxes', iconComponent: CheckSquare, items: [] },
      { type: 'radio', label: 'Radio Groups', iconComponent: Circle, items: [] },
      { type: 'radio_option', label: 'Radio Options', iconComponent: Circle, items: [] },
      { type: 'switch', label: 'Switches', iconComponent: ToggleRight, items: [] },
      { type: 'select', label: 'Dropdowns', iconComponent: ChevronsUpDown, items: [] },
      { type: 'select_option', label: 'Options', iconComponent: ListFilter, items: [] }
    ]

    let globalIdx = 0
    const typeMap = Object.fromEntries(groups.map(g => [g.type, g]))

    for (const item of filteredSuggestions.value) {
      const group = typeMap[item.type]
      if (group) {
        group.items.push({ ...item, _globalIdx: globalIdx++ })
      }
    }

    return groups.filter(g => g.items.length > 0)
  })

  const totalFilteredCount = computed(() => filteredSuggestions.value.length)

  function isItemSelected(item) {
    if (!props.modelValue) return false
    const vk = valueKey.value
    if (vk === 'selector') return item.selector === props.modelValue
    if (vk === 'value') return item.value === props.modelValue
    if (vk === 'text') return item.text === props.modelValue
    if (vk === 'name') return item.name === props.modelValue
    if (vk === 'id') return item.id === props.modelValue
    if (vk === 'label') return item.label === props.modelValue
    return (item.text || item.name || item.displayText) === props.modelValue
  }

  function selectItem(item, closeFn) {
    let val
    let switchMethod = null
    const vk = valueKey.value

    // Try to get value using the current method (valueKey)
    if (vk === 'selector') {
      val = item.selector
    } else if (vk === 'text' && item.text) {
      val = item.text
    } else if (vk === 'value' && item.value !== undefined) {
      val = item.value
    } else if (vk === 'placeholder' && item.placeholder) {
      val = item.placeholder
    } else if (vk === 'name' && item.name) {
      val = item.name
    } else if (vk === 'id' && item.id) {
      val = item.id
    } else if (vk === 'label' && item.label) {
      val = item.label
    } else {
      // Current method can't resolve this item. Find the best method+value pair
      // and switch method atomically with the value.
      if (item.text) { val = item.text; switchMethod = 'text' }
      else if (item.placeholder) { val = item.placeholder; switchMethod = 'placeholder' }
      else if (item.label) { val = item.label; switchMethod = 'label' }
      else if (item.name) { val = item.name; switchMethod = 'name' }
      else if (item.id) { val = item.id; switchMethod = 'id' }
      else if (item.selector) { val = item.selector; switchMethod = 'selector' }
      else { val = item.displayText || ''; switchMethod = null }
    }

    // Emit method switch + value as a single batch so the parent can update
    // localParams atomically (prevents showIf flicker from intermediate state)
    if (switchMethod && switchMethod !== vk) {
      emit('auto-switch-method', { method: switchMethod, value: val })
    } else {
      emit('update:value', val)
      emit('update:modelValue', val)
    }
    closeFn()
  }

  return {
    suggestions,
    hasSuggestions,
    isSelectMode,
    selectedDisplayLabel,
    toggleTitle,
    filteredSuggestions,
    groupedSuggestions,
    totalFilteredCount,
    isItemSelected,
    selectItem,
    valueKey,
  }
}

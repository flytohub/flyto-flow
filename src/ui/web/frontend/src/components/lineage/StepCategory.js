/**
 * Step Category Constants
 * Based on Data Lineage Spec for swimlane visualization
 */

export const StepCategory = {
  OBSERVE: 'observe',
  EVALUATE: 'evaluate',
  DECIDE: 'decide',
  ACT: 'act',
  VERIFY: 'verify'
}

export const CATEGORY_CONFIG = {
  [StepCategory.OBSERVE]: {
    label: 'Observe',
    color: '#3b82f6', // blue
    bgColor: 'rgba(59, 130, 246, 0.1)',
    borderColor: 'rgba(59, 130, 246, 0.3)',
    icon: 'Eye',
    description: 'Screenshots, API responses, data capture'
  },
  [StepCategory.EVALUATE]: {
    label: 'Evaluate',
    color: '#f59e0b', // amber
    bgColor: 'rgba(245, 158, 11, 0.1)',
    borderColor: 'rgba(245, 158, 11, 0.3)',
    icon: 'Calculator',
    description: 'Score calculation, validation'
  },
  [StepCategory.DECIDE]: {
    label: 'Decide',
    color: '#a855f7', // purple
    bgColor: 'rgba(168, 85, 247, 0.1)',
    borderColor: 'rgba(168, 85, 247, 0.3)',
    icon: 'Brain',
    description: 'AI decisions with confidence'
  },
  [StepCategory.ACT]: {
    label: 'Act',
    color: '#22c55e', // green
    bgColor: 'rgba(34, 197, 94, 0.1)',
    borderColor: 'rgba(34, 197, 94, 0.3)',
    icon: 'Play',
    description: 'Execute operations'
  },
  [StepCategory.VERIFY]: {
    label: 'Verify',
    color: '#06b6d4', // cyan
    bgColor: 'rgba(6, 182, 212, 0.1)',
    borderColor: 'rgba(6, 182, 212, 0.3)',
    icon: 'CheckCircle',
    description: 'Confirm results'
  }
}

export const CATEGORY_ORDER = [
  StepCategory.OBSERVE,
  StepCategory.EVALUATE,
  StepCategory.DECIDE,
  StepCategory.ACT,
  StepCategory.VERIFY
]

/**
 * Get category configuration
 */
export function getCategoryConfig(category) {
  return CATEGORY_CONFIG[category] || CATEGORY_CONFIG[StepCategory.ACT]
}

/**
 * Group steps by category for swimlane display
 */
export function groupStepsByCategory(steps) {
  const grouped = {}
  for (const category of CATEGORY_ORDER) {
    grouped[category] = []
  }

  for (const step of steps) {
    const category = step.category || StepCategory.ACT
    if (grouped[category]) {
      grouped[category].push(step)
    } else {
      grouped[StepCategory.ACT].push(step)
    }
  }

  return grouped
}

export default {
  StepCategory,
  CATEGORY_CONFIG,
  CATEGORY_ORDER,
  getCategoryConfig,
  groupStepsByCategory
}

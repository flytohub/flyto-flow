/**
 * Lineage Components
 *
 * Swimlane visualization for AI execution lineage.
 * Based on Data Lineage Spec with 3 layers:
 * - Storyline: 5 swimlanes (Observe → Evaluate → Decide → Act → Verify)
 * - Artifacts: Evidence and outputs (screenshot, report, decision, patch, diff, log)
 * - Debug: Full execution trace with timing
 */

export { default as StorylineView } from './StorylineView.vue'
export { default as DecisionNode } from './DecisionNode.vue'
export { default as LoopContainer } from './LoopContainer.vue'
export { default as StepCard } from './StepCard.vue'
export {
  StepCategory,
  CATEGORY_CONFIG,
  CATEGORY_ORDER,
  getCategoryConfig,
  groupStepsByCategory
} from './StepCategory'

export default {
  StorylineView: () => import('./StorylineView.vue'),
  DecisionNode: () => import('./DecisionNode.vue'),
  LoopContainer: () => import('./LoopContainer.vue'),
  StepCard: () => import('./StepCard.vue')
}

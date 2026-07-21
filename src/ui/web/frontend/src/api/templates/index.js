/**
 * Templates API - Main Entry Point
 *
 * Re-exports all template operations as a unified API object
 * for backward compatibility with existing code.
 */

// Import all modules
import * as crud from './crud'
import * as library from './library'
import * as reviews from './reviews'
import * as inviteKeys from './inviteKeys'
import * as purchases from './purchases'
import * as categories from './categories'
import * as pullRequests from './pullRequests'
import * as templateIssues from './templateIssues'
import * as folders from './folders'

// Re-export helpers for direct use
export { normalizeTemplate, getCurrentUserId, getCurrentUser } from './helpers'

// Unified API object (backward compatible)
export const templatesAPI = {
  // CRUD
  createTemplate: crud.createTemplate,
  updateTemplate: crud.updateTemplate,
  getTemplate: crud.getTemplate,
  listTemplates: crud.listTemplates,
  deleteTemplate: crud.deleteTemplate,
  searchTemplates: crud.searchTemplates,
  executeTemplate: crud.executeTemplate,
  updateMarketplaceListing: crud.updateMarketplaceListing,
  unpublishTemplate: crud.unpublishTemplate,

  // Library
  getLibrary: library.getLibrary,
  addToLibrary: library.addToLibrary,
  removeFromLibrary: library.removeFromLibrary,
  batchRemoveFromLibrary: library.batchRemoveFromLibrary,
  updateLibrarySettings: library.updateLibrarySettings,

  // My Templates (enhanced endpoint)
  listMyTemplates: crud.listMyTemplates,

  // Batch
  batchDeleteTemplates: crud.batchDeleteTemplates,

  // YAML Export/Import/Diff
  exportYAML: crud.exportYAML,
  importYAML: crud.importYAML,
  pushYAML: crud.pushYAML,
  pullYAML: crud.pullYAML,
  diffYAML: crud.diffYAML,
  diffVersionsYAML: crud.diffVersionsYAML,

  // Reviews
  getReviews: reviews.getReviews,
  addReview: reviews.addReview,
  updateReview: reviews.updateReview,
  deleteReview: reviews.deleteReview,

  // Invite Keys
  createInviteKey: inviteKeys.createInviteKey,
  listInviteKeys: inviteKeys.listInviteKeys,
  redeemInviteKey: inviteKeys.redeemInviteKey,
  revokeInviteKey: inviteKeys.revokeInviteKey,

  // Purchases
  syncPurchase: purchases.syncPurchase,

  // Forks
  forkTemplate: purchases.forkTemplate,
  getForkSyncStatus: purchases.getForkSyncStatus,
  syncForkWithUpstream: purchases.syncForkWithUpstream,

  // Merge Settings
  updateMergeSettings: purchases.updateMergeSettings,

  // Tags
  getAvailableTags: crud.getAvailableTags,

  // Categories
  getCategories: categories.getCategories,

  // Pull Requests
  listPullRequests: pullRequests.listPullRequests,
  getPullRequest: pullRequests.getPullRequest,
  createPullRequest: pullRequests.createPullRequest,
  reviewPullRequest: pullRequests.reviewPullRequest,
  mergePullRequest: pullRequests.mergePullRequest,
  closePullRequest: pullRequests.closePullRequest,
  reopenPullRequest: pullRequests.reopenPullRequest,
  markPRReady: pullRequests.markPRReady,
  updatePRLabels: pullRequests.updatePRLabels,
  listPRComments: pullRequests.listPRComments,
  createPRComment: pullRequests.createPRComment,
  updatePRComment: pullRequests.updatePRComment,
  deletePRComment: pullRequests.deletePRComment,
  togglePRReaction: pullRequests.togglePRReaction,
  togglePRCommentReaction: pullRequests.togglePRCommentReaction,
  mergeCheck: pullRequests.mergeCheck,
  linkIssueToPR: pullRequests.linkIssueToPR,

  // Template Issues
  listTemplateIssues: templateIssues.listIssues,
  getTemplateIssue: templateIssues.getIssue,
  createTemplateIssue: templateIssues.createIssue,
  updateTemplateIssue: templateIssues.updateIssue,
  closeTemplateIssue: templateIssues.closeIssue,
  reopenTemplateIssue: templateIssues.reopenIssue,
  toggleTemplateIssueUpvote: templateIssues.toggleUpvote,
  updateIssueAssignees: templateIssues.updateAssignees,
  linkPRToIssue: templateIssues.linkPRToIssue,
  listTemplateIssueComments: templateIssues.listComments,
  createTemplateIssueComment: templateIssues.createComment,
  updateTemplateIssueComment: templateIssues.updateComment,
  deleteTemplateIssueComment: templateIssues.deleteComment,
  toggleIssueReaction: templateIssues.toggleIssueReaction,
  toggleIssueCommentReaction: templateIssues.toggleIssueCommentReaction,

  // Folders
  listFolders: folders.listFolders,
  createFolder: folders.createFolder,
  updateFolder: folders.updateFolder,
  deleteFolder: folders.deleteFolder,
  moveToFolder: folders.moveToFolder,
  reorderFolders: folders.reorderFolders,
}

// Named exports for tree-shaking
export {
  // CRUD
  crud,
  library,
  reviews,
  inviteKeys,
  purchases,
  categories,
  pullRequests,
  templateIssues,
  folders,
}

export default templatesAPI

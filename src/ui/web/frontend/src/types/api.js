/**
 * API Contract Type Definitions
 *
 * JSDoc type definitions for API requests and responses.
 * These types define the contract between frontend and backend.
 *
 * Naming Convention:
 * - Backend (Python): snake_case
 * - Frontend (JS): camelCase
 * - Use transformApiResponse/transformApiRequest from @/utils/caseConverter for conversion
 */

// ============================================================================
// Common Types
// ============================================================================

/**
 * @typedef {Object} ApiResponse
 * @property {boolean} ok - Whether the request succeeded
 * @property {string} [message] - Success message
 * @property {string} [error] - Error message
 * @property {Object} [data] - Response data
 */

/**
 * @typedef {Object} PaginatedResponse
 * @property {Array} items - List of items
 * @property {number} total - Total count
 * @property {number} page - Current page
 * @property {number} page_size - Items per page
 * @property {boolean} has_more - Whether more pages exist
 */

/**
 * @typedef {'free'|'pro'|'team'|'offline'|'enterprise'} SubscriptionPlan
 */

/**
 * @typedef {'active'|'trialing'|'past_due'|'canceled'|'unpaid'} SubscriptionStatus
 */

// ============================================================================
// User Types
// ============================================================================

/**
 * @typedef {Object} User
 * @property {string} id - User ID
 * @property {string} email - User email
 * @property {string} [display_name] - Display name
 * @property {string} [photo_url] - Profile photo URL
 * @property {boolean} is_admin - Whether user is admin
 * @property {SubscriptionPlan} subscription_plan - Current subscription plan
 * @property {SubscriptionStatus} subscription_status - Subscription status
 * @property {string} [subscription_tier] - Legacy tier field
 * @property {string} created_at - ISO timestamp
 * @property {string} [updated_at] - ISO timestamp
 */

/**
 * @typedef {Object} UserProfile
 * @property {string} id
 * @property {string} email
 * @property {string} [display_name]
 * @property {string} [photo_url]
 * @property {string} [bio]
 * @property {string} [website]
 * @property {Object} preferences - User preferences
 */

// ============================================================================
// Capabilities Types
// ============================================================================

/**
 * @typedef {'saas_cloud'|'local_online'|'local_offline'|'enterprise_intranet'} DeploymentMode
 */

/**
 * @typedef {'free'|'subscription'|'offline_license'|'enterprise'} LicenseType
 */

/**
 * @typedef {Object} CapabilitiesResponse
 * @property {DeploymentMode} deployment_mode - Current deployment mode
 * @property {LicenseType} license_type - Current license type
 * @property {boolean} is_licensed - Whether system is licensed
 * @property {string[]} capabilities - List of capability strings
 * @property {Object} features - Feature flags
 * @property {boolean} features.marketplace - Marketplace enabled
 * @property {boolean} features.billing - Billing enabled
 * @property {boolean} features.observability - Observability enabled
 * @property {boolean} features.versioning - Versioning enabled
 * @property {boolean} features.audit - Audit enabled
 * @property {Object} pages - Page access configuration
 * @property {Object} ui - UI configuration
 * @property {boolean} ui.showMarketplace - Show marketplace in nav
 * @property {boolean} ui.showObservability - Show observability in nav
 * @property {boolean} ui.canUpgrade - Show upgrade prompts
 */

// ============================================================================
// Template Types
// ============================================================================

/**
 * @typedef {Object} Template
 * @property {string} id - Template ID
 * @property {string} name - Template name
 * @property {string} [description] - Description
 * @property {string} creator_id - Creator user ID
 * @property {string} [creator_name] - Creator display name
 * @property {'draft'|'published'|'archived'} status - Template status
 * @property {'public'|'private'|'unlisted'} visibility - Visibility
 * @property {boolean} listed - Listed in marketplace
 * @property {Object} workflow - Workflow definition
 * @property {Object[]} sections - UI sections
 * @property {string} created_at - ISO timestamp
 * @property {string} updated_at - ISO timestamp
 * @property {number} [view_count] - View count
 * @property {number} [run_count] - Run count
 * @property {number} [average_rating] - Average rating
 */

/**
 * @typedef {Object} TemplateListItem
 * @property {string} id
 * @property {string} name
 * @property {string} [description]
 * @property {string} creator_id
 * @property {string} [creator_name]
 * @property {string} [thumbnail_url]
 * @property {string} updated_at
 * @property {number} [run_count]
 * @property {number} [average_rating]
 */

// ============================================================================
// Workflow Types
// ============================================================================

/**
 * @typedef {Object} WorkflowNode
 * @property {string} id - Node ID
 * @property {string} type - Module type (e.g., 'browser.launch')
 * @property {Object} position - Node position
 * @property {number} position.x - X coordinate
 * @property {number} position.y - Y coordinate
 * @property {Object} data - Node data
 * @property {string} data.label - Display label
 * @property {Object} data.params - Module parameters
 */

/**
 * @typedef {Object} WorkflowEdge
 * @property {string} id - Edge ID
 * @property {string} source - Source node ID
 * @property {string} target - Target node ID
 * @property {string} [sourceHandle] - Source handle ID
 * @property {string} [targetHandle] - Target handle ID
 * @property {string} [type] - Edge type
 */

/**
 * @typedef {Object} Workflow
 * @property {string} name - Workflow name
 * @property {string} [version] - Version string
 * @property {Object[]} steps - Workflow steps
 * @property {string} steps[].id - Step ID
 * @property {string} steps[].module - Module ID
 * @property {Object} steps[].params - Step parameters
 */

// ============================================================================
// Execution Types
// ============================================================================

/**
 * @typedef {'pending'|'running'|'completed'|'failed'|'cancelled'} ExecutionStatus
 */

/**
 * @typedef {Object} Execution
 * @property {string} id - Execution ID
 * @property {string} workflow_id - Workflow/Template ID
 * @property {string} [workflow_name] - Workflow name
 * @property {ExecutionStatus} status - Current status
 * @property {string} [user_id] - User who started execution
 * @property {string} start_time - ISO timestamp
 * @property {string} [end_time] - ISO timestamp
 * @property {number} [duration_ms] - Duration in milliseconds
 * @property {Object} [result] - Execution result
 * @property {string} [error] - Error message if failed
 * @property {number} step_count - Total steps
 * @property {number} completed_steps - Completed steps
 */

/**
 * @typedef {Object} ExecutionStep
 * @property {string} step_id - Step ID
 * @property {number} step_index - Step index (0-based)
 * @property {string} module_id - Module ID
 * @property {Object} params - Step parameters
 * @property {ExecutionStatus} status - Step status
 * @property {number} [duration_ms] - Duration in milliseconds
 * @property {Object} [result] - Step result
 * @property {string} [error] - Error message
 * @property {string} timestamp - ISO timestamp
 */

// ============================================================================
// Replay Types
// ============================================================================

/**
 * @typedef {Object} ReplayValidateRequest
 * @property {string} execution_id - Original execution ID
 * @property {string} step_id - Step to replay from
 * @property {string} [end_step_id] - Optional end step
 * @property {string[]} skip_steps - Steps to skip
 */

/**
 * @typedef {Object} ReplayValidateResponse
 * @property {boolean} can_replay - Whether replay is possible
 * @property {string} [reason] - Reason if can't replay
 * @property {string} execution_id
 * @property {string} step_id
 * @property {number} step_index
 * @property {string} module_id
 * @property {number} total_steps
 * @property {number} remaining_steps
 * @property {boolean} context_available
 * @property {string[]} context_keys
 */

/**
 * @typedef {Object} ReplayExecuteRequest
 * @property {string} execution_id - Original execution ID
 * @property {string} [step_id] - Step to replay from (null = full replay)
 * @property {string} [end_step_id] - Optional end step
 * @property {Object} modified_context - Context modifications
 * @property {string[]} skip_steps - Steps to skip
 * @property {string[]} breakpoints - Breakpoint step IDs
 * @property {boolean} dry_run - Just prepare, don't execute
 */

/**
 * @typedef {Object} ReplayExecuteResponse
 * @property {boolean} ok
 * @property {string} [replay_id] - New execution ID
 * @property {boolean} [executed] - Whether actually executed
 * @property {string} [message]
 * @property {string} [error]
 * @property {string} from_step
 * @property {number} [from_step_index]
 * @property {string[]} context_keys
 */

// ============================================================================
// Module Types
// ============================================================================

/**
 * @typedef {'DANGEROUS'|'ELEVATED'|'SAFE'} ModuleSecurityLevel
 */

/**
 * @typedef {Object} ModuleParam
 * @property {string} name - Parameter name
 * @property {string} type - Parameter type
 * @property {string} [description] - Description
 * @property {boolean} required - Whether required
 * @property {*} [default] - Default value
 * @property {*[]} [enum] - Allowed values
 */

/**
 * @typedef {Object} ModuleMetadata
 * @property {string} id - Module ID (e.g., 'browser.launch')
 * @property {string} name - Display name
 * @property {string} [description] - Description
 * @property {string} category - Category name
 * @property {ModuleSecurityLevel} security_level - Security classification
 * @property {string[]} [input_types] - Accepted input types
 * @property {string[]} [output_types] - Output types
 * @property {string[]} [can_receive_from] - Module patterns that can connect
 * @property {string[]} [can_connect_to] - Modules this can connect to
 * @property {ModuleParam[]} params - Parameter definitions
 * @property {Object} [handles] - Port definitions
 */

// ============================================================================
// Lineage Types
// ============================================================================

/**
 * @typedef {Object} LineageNode
 * @property {string} id - Node ID
 * @property {string} step_id - Step ID
 * @property {string} [module_id] - Module ID
 * @property {string} status - Execution status
 * @property {number} [duration_ms]
 * @property {string} [error]
 */

/**
 * @typedef {Object} LineageEdge
 * @property {string} source - Source node ID
 * @property {string} target - Target node ID
 * @property {string} [label] - Edge label
 */

/**
 * @typedef {Object} LineageGraphResponse
 * @property {LineageNode[]} nodes
 * @property {LineageEdge[]} edges
 * @property {Object} metadata
 */

// ============================================================================
// Audit Types
// ============================================================================

/**
 * @typedef {Object} AuditEntry
 * @property {string} id - Entry ID
 * @property {string} timestamp - ISO timestamp
 * @property {string} action - Action type
 * @property {string} [user_id] - User who performed action
 * @property {string} [user_email] - User email
 * @property {string} [resource_type] - Resource type
 * @property {string} [resource_id] - Resource ID
 * @property {Object} [details] - Action details
 * @property {string} [ip_address] - Client IP
 * @property {string} hash - Entry hash for chain verification
 * @property {string} [previous_hash] - Previous entry hash
 */

// ============================================================================
// Admin Types
// ============================================================================

/**
 * @typedef {Object} AdminUser
 * @property {string} id - User ID
 * @property {string} uid - User ID (alias)
 * @property {string} email - User email
 * @property {string} [display_name] - Display name
 * @property {string} role - User role
 * @property {boolean} is_admin - Admin flag
 * @property {boolean} is_creator - Creator flag
 * @property {boolean} stripe_connected - Has Stripe account
 * @property {SubscriptionPlan} subscription_plan - Subscription plan
 * @property {SubscriptionPlan} subscription_tier - Subscription tier (alias)
 * @property {SubscriptionStatus} subscription_status - Subscription status
 * @property {string[]} allowed_languages - Allowed languages
 * @property {string} created_at - ISO timestamp
 */

/**
 * @typedef {Object} AdminUsersResponse
 * @property {boolean} ok - Success flag
 * @property {AdminUser[]} users - User list
 * @property {number} total - Total count
 * @property {number} page - Current page
 * @property {number} page_size - Page size
 */

/**
 * @typedef {Object} RevenueBreakdown
 * @property {number} template_sales - Template sales revenue
 * @property {number} subscriptions - Subscription revenue
 * @property {number} offline_licenses - Offline license revenue
 * @property {number} total - Total revenue
 */

/**
 * @typedef {Object} RevenueStatsResponse
 * @property {string[]} labels - Date labels
 * @property {number[]} total_revenue - Daily revenue
 * @property {number[]} sales_count - Daily sales count
 * @property {number[]} platform_earnings - Daily platform earnings
 * @property {number} platform_fee_percent - Platform fee percentage
 * @property {RevenueBreakdown} breakdown - Revenue breakdown
 */

/**
 * @typedef {Object} AdminStatsResponse
 * @property {boolean} ok - Success flag
 * @property {number} total_users - Total users
 * @property {number} total_templates - Total templates
 * @property {number} total_revenue - Total revenue
 * @property {number} total_sales - Total sales
 */

// ============================================================================
// Chat Types
// ============================================================================

/**
 * @typedef {'text'|'image'|'file'|'system'|'order'} MessageType
 */

/**
 * Chat Message - Frontend normalized format (camelCase)
 * @typedef {Object} ChatMessage
 * @property {string} id - Message ID
 * @property {string} conversationId - Conversation ID
 * @property {string} senderId - Sender user ID
 * @property {MessageType} messageType - Message type
 * @property {string} content - Message content
 * @property {string} [attachmentUrl] - Attachment URL (for image/file)
 * @property {string} [attachmentName] - Attachment filename
 * @property {number} [attachmentSize] - Attachment size in bytes
 * @property {string} [orderId] - Order ID (for order messages)
 * @property {Object} [order] - Order object (enriched)
 * @property {string[]} readBy - User IDs who have read the message
 * @property {string} [readAt] - ISO timestamp when read
 * @property {string} createdAt - ISO timestamp
 */

/**
 * Chat Conversation - Frontend normalized format (camelCase)
 * @typedef {Object} ChatConversation
 * @property {string} id - Conversation ID
 * @property {string[]} participantIds - Participant user IDs
 * @property {string} [lastMessage] - Last message preview
 * @property {string} [lastMessageAt] - ISO timestamp
 * @property {string} [lastSenderId] - Last message sender ID
 * @property {Object.<string, number>} unreadCounts - Unread count per user
 * @property {number} unreadCount - Current user's unread count
 * @property {boolean} isArchived - Is conversation archived
 * @property {string} createdAt - ISO timestamp
 * @property {string} updatedAt - ISO timestamp
 * @property {ChatUserBrief} [otherUser] - Other participant info
 * @property {Object.<string, ChatUserBrief>} [participantInfo] - All participants info
 * @property {string} [currentUserId] - Current user ID
 */

/**
 * Brief user info for chat
 * @typedef {Object} ChatUserBrief
 * @property {string} id - User ID
 * @property {string} [name] - Display name
 * @property {string} [avatar] - Avatar URL
 * @property {string} [email] - Email
 */

// ============================================================================
// User Types (Updated for camelCase consistency)
// ============================================================================

/**
 * User - Frontend normalized format (camelCase)
 * @typedef {Object} NormalizedUser
 * @property {string} id - User ID
 * @property {string} uid - User ID (alias)
 * @property {string} email - User email
 * @property {string} [displayName] - Display name
 * @property {string} [avatarUrl] - Profile photo URL
 * @property {string} [bio] - User bio
 * @property {string} [website] - User website
 * @property {boolean} isAdmin - Whether user is admin
 * @property {boolean} isPro - Whether user has pro subscription
 * @property {string[]} roles - User roles
 * @property {string[]} allowedLanguages - Allowed languages
 * @property {SubscriptionPlan} subscriptionPlan - Current subscription plan
 * @property {SubscriptionStatus} subscriptionStatus - Subscription status
 * @property {string} createdAt - ISO timestamp
 * @property {string} [updatedAt] - ISO timestamp
 * @property {number} [followersCount] - Follower count
 * @property {number} [followingCount] - Following count
 */

// ============================================================================
// Export all types for IDE support
// ============================================================================

export const API_TYPES = {
  // This is a type-only module, no runtime exports needed
  // Types are available via JSDoc @typedef above
}

export default API_TYPES

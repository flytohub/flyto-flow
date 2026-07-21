"""
Unified Data Models (DTOs)

These models define the unified interface for data across all deployment modes.
Each provider must map its data source to these structures.
"""

# Common models
from gateway.providers.data.models.common import (
    DataSource,
    PaginatedResponse,
    paginate,
    empty_page,
)

# Workflow models
from gateway.providers.data.models.workflow import (
    TriggerType,
    WorkflowNode,
    WorkflowEdge,
    WorkflowDTO,
    WorkflowCreateDTO,
    WorkflowUpdateDTO,
)

# Template models
from gateway.providers.data.models.template import (
    TemplateDTO,
    TemplateCreateDTO,
    TemplateUpdateDTO,
    TemplateVersionDTO,
    PurchaseSnapshotDTO,
    ForkTemplateDTO,
    LibrarySettingsUpdateDTO,
)

# Execution models
from gateway.providers.data.models.execution import (
    ExecutionStatus,
    ExecutionDTO,
)

# Chat models
from gateway.providers.data.models.chat import (
    MessageType,
    ConversationDTO,
    ConversationCreateDTO,
    MessageDTO,
    MessageCreateDTO,
)

# User models
from gateway.providers.data.models.user import (
    UserProfileDTO,
    UserProfileUpdateDTO,
    FollowDTO,
)

# Notification models
from gateway.providers.data.models.notification import (
    NotificationType,
    NotificationDTO,
    NotificationCreateDTO,
)

# Storage models
from gateway.providers.data.models.storage import (
    FileUploadDTO,
    FileUploadRequestDTO,
)

# Review models
from gateway.providers.data.models.review import (
    ReviewDTO,
    ReviewCreateDTO,
    ReviewUpdateDTO,
    ReviewStatsDTO,
)

# Subscription models
from gateway.providers.data.models.subscription import (
    SubscriptionPlan,
    SubscriptionStatus,
    SubscriptionDTO,
    SubscriptionCreateDTO,
)

# Earnings models
from gateway.providers.data.models.earnings import (
    EarningStatus,
    EarningDTO,
    EarningsSummaryDTO,
    PayoutDTO,
)

# Payment models
from gateway.providers.data.models.payment import (
    CheckoutSessionDTO,
    PayoutSettingsDTO,
    PayoutSettingsUpdateDTO,
)

# AI Usage models
from gateway.providers.data.models.ai_usage import (
    AIUsageDTO,
    AIUsageRecordDTO,
)

# Audit models
from gateway.providers.data.models.audit import (
    AuditAction,
    AuditLogDTO,
    AuditLogCreateDTO,
)

# Deletion models
from gateway.providers.data.models.deletion import (
    DeletionRequestStatus,
    DeletionRequestDTO,
    DeletionRequestCreateDTO,
)

# User Tool models
from gateway.providers.data.models.user_tool import (
    UserToolDTO,
    UserToolCreateDTO,
    UserToolUpdateDTO,
)

# Order models
from gateway.providers.data.models.order import (
    OrderStatus,
    OrderDTO,
    OrderCreateDTO,
    OrderUpdateDTO,
)

# Invite Key models
from gateway.providers.data.models.invite_key import (
    InviteKeyDTO,
    InviteKeyCreateDTO,
    InviteKeyBatchCreateDTO,
    InviteKeyStatsDTO,
)

# Report models
from gateway.providers.data.models.report import (
    ReportStatus,
    ReportType,
    ReportDTO,
    ReportCreateDTO,
    ReportUpdateDTO,
)

# Issue models
from gateway.providers.data.models.issue import (
    IssueType,
    IssueStatus,
    IssuePriority,
    IssueDTO,
    IssueCreateDTO,
    IssueUpdateDTO,
    IssueCommentDTO,
    IssueCommentCreateDTO,
)

# Pull Request models
from gateway.providers.data.models.pull_request import (
    PRStatus,
    PullRequestDTO,
    PullRequestCreateDTO,
    PullRequestSummaryDTO,
    PRCommentDTO,
    PRCommentCreateDTO,
)

# Template Issue models
from gateway.providers.data.models.template_issue import (
    TemplateIssueType,
    TemplateIssueStatus,
    TemplateIssueDTO,
    TemplateIssueCreateDTO,
    TemplateIssueCommentDTO,
    TemplateIssueCommentCreateDTO,
)

# API Key models
from gateway.providers.data.models.api_key import (
    ApiKeyDTO,
    ApiKeyCreateDTO,
    ApiKeyUpdateDTO,
    ApiKeyVerifyResult,
)

# Fee Transaction models (for tax compliance)
from gateway.providers.data.models.fee_transaction import (
    TransactionType,
    TransactionStatus,
    FeeTransactionDTO,
    FeeTransactionCreateDTO,
    FeeCalculation,
)

# Wallet / Credits models
from gateway.providers.data.models.wallet import (
    CreditTransactionType,
    CreditTransactionDTO,
)

__all__ = [
    # Common
    'DataSource',
    'PaginatedResponse',
    'paginate',
    'empty_page',
    # Workflow
    'TriggerType',
    'WorkflowNode',
    'WorkflowEdge',
    'WorkflowDTO',
    'WorkflowCreateDTO',
    'WorkflowUpdateDTO',
    # Template
    'TemplateDTO',
    'TemplateCreateDTO',
    'TemplateUpdateDTO',
    'TemplateVersionDTO',
    'PurchaseSnapshotDTO',
    'ForkTemplateDTO',
    'LibrarySettingsUpdateDTO',
    # Execution
    'ExecutionStatus',
    'ExecutionDTO',
    # Chat
    'MessageType',
    'ConversationDTO',
    'ConversationCreateDTO',
    'MessageDTO',
    'MessageCreateDTO',
    # User
    'UserProfileDTO',
    'UserProfileUpdateDTO',
    'FollowDTO',
    # Notification
    'NotificationType',
    'NotificationDTO',
    'NotificationCreateDTO',
    # Storage
    'FileUploadDTO',
    'FileUploadRequestDTO',
    # Review
    'ReviewDTO',
    'ReviewCreateDTO',
    'ReviewUpdateDTO',
    'ReviewStatsDTO',
    # Subscription
    'SubscriptionPlan',
    'SubscriptionStatus',
    'SubscriptionDTO',
    'SubscriptionCreateDTO',
    # Earnings
    'EarningStatus',
    'EarningDTO',
    'EarningsSummaryDTO',
    'PayoutDTO',
    # Payment
    'CheckoutSessionDTO',
    'PayoutSettingsDTO',
    'PayoutSettingsUpdateDTO',
    # AI Usage
    'AIUsageDTO',
    'AIUsageRecordDTO',
    # Audit
    'AuditAction',
    'AuditLogDTO',
    'AuditLogCreateDTO',
    # Deletion
    'DeletionRequestStatus',
    'DeletionRequestDTO',
    'DeletionRequestCreateDTO',
    # User Tool
    'UserToolDTO',
    'UserToolCreateDTO',
    'UserToolUpdateDTO',
    # Order
    'OrderStatus',
    'OrderDTO',
    'OrderCreateDTO',
    'OrderUpdateDTO',
    # Invite Key
    'InviteKeyDTO',
    'InviteKeyCreateDTO',
    'InviteKeyBatchCreateDTO',
    'InviteKeyStatsDTO',
    # Report
    'ReportStatus',
    'ReportType',
    'ReportDTO',
    'ReportCreateDTO',
    'ReportUpdateDTO',
    # Issue
    'IssueType',
    'IssueStatus',
    'IssuePriority',
    'IssueDTO',
    'IssueCreateDTO',
    'IssueUpdateDTO',
    'IssueCommentDTO',
    'IssueCommentCreateDTO',
    # API Key
    'ApiKeyDTO',
    'ApiKeyCreateDTO',
    'ApiKeyUpdateDTO',
    'ApiKeyVerifyResult',
    # Fee Transaction
    'TransactionType',
    'TransactionStatus',
    'FeeTransactionDTO',
    'FeeTransactionCreateDTO',
    'FeeCalculation',
    # Wallet / Credits
    'CreditTransactionType',
    'CreditTransactionDTO',
    # Pull Request
    'PRStatus',
    'PullRequestDTO',
    'PullRequestCreateDTO',
    'PullRequestSummaryDTO',
    'PRCommentDTO',
    'PRCommentCreateDTO',
    # Template Issue
    'TemplateIssueType',
    'TemplateIssueStatus',
    'TemplateIssueDTO',
    'TemplateIssueCreateDTO',
    'TemplateIssueCommentDTO',
    'TemplateIssueCommentCreateDTO',
]

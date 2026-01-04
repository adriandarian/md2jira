"""
Ports - Abstract interfaces for external dependencies.

Ports define the contracts that adapters must implement.
This enables dependency inversion and easy testing.
"""

from .async_tracker import AsyncIssueTrackerPort
from .config_provider import ConfigProviderPort
from .document_formatter import DocumentFormatterPort
from .document_output import (
    AuthenticationError as OutputAuthenticationError,
)
from .document_output import (
    DocumentOutputError,
    DocumentOutputPort,
)
from .document_output import (
    NotFoundError as OutputNotFoundError,
)
from .document_output import (
    PermissionError as OutputPermissionError,
)
from .document_output import (
    RateLimitError as OutputRateLimitError,
)
from .document_parser import DocumentParserPort, ParserError
from .graphql_api import (
    Connection,
    Edge,
    ErrorCode,
    ExecutionContext,
    GraphQLError,
    GraphQLRequest,
    GraphQLResponse,
    GraphQLServerPort,
    OperationType,
    PageInfo,
    ResolverRegistry,
    ServerConfig,
    SubscriptionEvent,
)
from .graphql_api import (
    ServerStats as GraphQLServerStats,
)
from .issue_tracker import (
    AuthenticationError,
    IssueTrackerError,
    IssueTrackerPort,
    NotFoundError,
    PermissionError,
    RateLimitError,
    TransientError,
    TransitionError,
)
from .plugin_marketplace import (
    AuthenticationError as MarketplaceAuthError,
)
from .plugin_marketplace import (
    InstallationError,
    InstallResult,
    MarketplaceInfo,
    MarketplacePlugin,
    PluginAuthor,
    PluginCategory,
    PluginMarketplaceError,
    PluginMarketplacePort,
    PluginNotFoundError,
    PluginStatus,
    PluginVersionInfo,
    PublishError,
    PublishResult,
    SearchQuery,
    SearchResult,
)
from .state_store import (
    ConnectionError as StateConnectionError,
)
from .state_store import (
    MigrationError,
    QuerySortField,
    QuerySortOrder,
    StateQuery,
    StateStoreError,
    StateStorePort,
    StateSummary,
    StoreInfo,
)
from .state_store import (
    TransactionError as StateTransactionError,
)
from .sync_history import (
    ChangeRecord,
    HistoryQuery,
    HistoryStoreInfo,
    RollbackError,
    SyncHistoryEntry,
    SyncHistoryError,
    SyncHistoryPort,
    SyncOutcome,
    SyncStatistics,
    VelocityMetrics,
)
from .websocket import (
    BroadcastError,
    ConnectionInfo,
    MessageType,
    RoomError,
    ServerStats,
    WebSocketError,
    WebSocketMessage,
    WebSocketServerPort,
)
from .websocket import (
    ConnectionError as WebSocketConnectionError,
)


__all__ = [
    "AsyncIssueTrackerPort",
    "AuthenticationError",
    "ConfigProviderPort",
    "DocumentFormatterPort",
    # Output exceptions
    "DocumentOutputError",
    "DocumentOutputPort",
    "DocumentParserPort",
    # Issue tracker exceptions
    "IssueTrackerError",
    # Ports
    "IssueTrackerPort",
    "MigrationError",
    "NotFoundError",
    "OutputAuthenticationError",
    "OutputNotFoundError",
    "OutputPermissionError",
    "OutputRateLimitError",
    # Parser exceptions
    "ParserError",
    "PermissionError",
    "QuerySortField",
    "QuerySortOrder",
    "RateLimitError",
    # State store
    "StateConnectionError",
    "StateQuery",
    "StateStoreError",
    "StateStorePort",
    "StateSummary",
    "StateTransactionError",
    "StoreInfo",
    # Sync history
    "ChangeRecord",
    "HistoryQuery",
    "HistoryStoreInfo",
    "RollbackError",
    "SyncHistoryEntry",
    "SyncHistoryError",
    "SyncHistoryPort",
    "SyncOutcome",
    "SyncStatistics",
    "VelocityMetrics",
    # Plugin marketplace
    "InstallationError",
    "InstallResult",
    "MarketplaceAuthError",
    "MarketplaceInfo",
    "MarketplacePlugin",
    "PluginAuthor",
    "PluginCategory",
    "PluginMarketplaceError",
    "PluginMarketplacePort",
    "PluginNotFoundError",
    "PluginStatus",
    "PluginVersionInfo",
    "PublishError",
    "PublishResult",
    "SearchQuery",
    "SearchResult",
    "TransientError",
    "TransitionError",
    # WebSocket
    "BroadcastError",
    "ConnectionInfo",
    "MessageType",
    "RoomError",
    "ServerStats",
    "WebSocketConnectionError",
    "WebSocketError",
    "WebSocketMessage",
    "WebSocketServerPort",
    # GraphQL API
    "Connection",
    "Edge",
    "ErrorCode",
    "ExecutionContext",
    "GraphQLError",
    "GraphQLRequest",
    "GraphQLResponse",
    "GraphQLServerPort",
    "GraphQLServerStats",
    "OperationType",
    "PageInfo",
    "ResolverRegistry",
    "ServerConfig",
    "SubscriptionEvent",
]

"""
Sync Module - Orchestration of synchronization between markdown and issue tracker.
"""

from .audit import AuditEntry, AuditTrail, AuditTrailRecorder, create_audit_trail
from .backup import (
    Backup,
    BackupManager,
    IssueSnapshot,
    RestoreOperation,
    RestoreResult,
    create_pre_sync_backup,
    restore_from_backup,
)
from .bidirectional import (
    BidirectionalSyncOrchestrator,
    BidirectionalSyncResult,
)
from .conflict import (
    Conflict,
    ConflictDetector,
    ConflictReport,
    ConflictResolution,
    ConflictResolver,
    ConflictType,
    FieldSnapshot,
    ResolutionStrategy,
    SnapshotStore,
    StorySnapshot,
    SyncSnapshot,
    create_snapshot_from_sync,
)
from .delta import (
    ChangeDirection,
    DeltaSyncResult,
    DeltaTracker,
    FieldChange,
    StoryDelta,
    SyncableField,
    create_delta_tracker,
)
from .diff import (
    DiffCalculator,
    DiffFormatter,
    DiffResult,
    FieldDiff,
    IssueDiff,
    compare_backup_to_current,
)
from .idempotency import (
    ContentHasher,
    IdempotencyCheck,
    IdempotencyGuard,
    IdempotencyLog,
    IdempotencyResult,
    IdempotencyStatus,
    check_idempotency,
    is_content_unchanged,
)
from .incremental import (
    ChangeDetectionResult,
    ChangeTracker,
    IncrementalSyncStats,
    StoryFingerprint,
    compute_story_hash,
    stories_differ,
)
from .links import (
    LinkChange,
    LinkSyncOrchestrator,
    LinkSyncResult,
)
from .merge import (
    MergeAttempt,
    MergeConfig,
    MergeResult,
    MergeStrategy,
    SmartMergeResolver,
    ThreeWayMerger,
    resolve_conflict_with_merge,
)
from .multi_epic import (
    EpicSyncResult,
    MultiEpicSyncOrchestrator,
    MultiEpicSyncResult,
)
from .multi_tracker import (
    MultiTrackerSyncOrchestrator,
    MultiTrackerSyncResult,
    SyncStrategy,
    TrackerSyncStatus,
    TrackerTarget,
    TrackerType,
    create_multi_tracker_orchestrator,
)
from .orchestrator import FailedOperation, SyncOrchestrator, SyncResult
from .progress import (
    ProgressCallback,
    ProgressReporter,
    ProgressState,
    create_progress_reporter,
)
from .progress import (
    SyncPhase as ProgressSyncPhase,
)
from .reverse_sync import (
    ChangeDetail,
    PullChanges,
    PullResult,
    ReverseSyncOrchestrator,
)
from .source_updater import (
    EpicTrackerInfo,
    SourceFileUpdater,
    SourceUpdateResult,
    SubtaskTrackerInfo,
    SyncStatus,
    TrackerInfo,
    compute_content_hash,
    compute_story_content_hash,
    detect_sync_conflicts,
)
from .state import OperationRecord, StateStore, SyncPhase, SyncState
from .transaction import OperationType as TransactionOperationType
from .transaction import (
    RollbackResult,
    TransactionalSync,
    TransactionManager,
    TransactionResult,
    TransactionState,
    create_transactional_sync,
)


# Parallel operations (optional, requires aiohttp)
try:
    from .parallel import (
        ParallelSyncOperations,
        ParallelSyncResult,
        is_parallel_available,
    )

    PARALLEL_AVAILABLE = True
except ImportError:
    PARALLEL_AVAILABLE = False

__all__ = [
    "PARALLEL_AVAILABLE",
    "AuditEntry",
    "AuditTrail",
    "AuditTrailRecorder",
    "Backup",
    "BackupManager",
    "BidirectionalSyncOrchestrator",
    "BidirectionalSyncResult",
    "ChangeDetail",
    "ChangeDetectionResult",
    "ChangeDirection",
    "ChangeTracker",
    "Conflict",
    "ConflictDetector",
    "ConflictReport",
    "ConflictResolution",
    "ConflictResolver",
    "ConflictType",
    "ContentHasher",
    "DeltaSyncResult",
    "DeltaTracker",
    "DiffCalculator",
    "DiffFormatter",
    "DiffResult",
    "EpicSyncResult",
    "EpicTrackerInfo",
    "FailedOperation",
    "FieldChange",
    "FieldDiff",
    "FieldSnapshot",
    "IdempotencyCheck",
    "IdempotencyGuard",
    "IdempotencyLog",
    "IdempotencyResult",
    "IdempotencyStatus",
    "IncrementalSyncStats",
    "IssueDiff",
    "IssueSnapshot",
    "LinkChange",
    "LinkSyncOrchestrator",
    "LinkSyncResult",
    "MergeAttempt",
    "MergeConfig",
    "MergeResult",
    "MergeStrategy",
    "MultiEpicSyncOrchestrator",
    "MultiEpicSyncResult",
    "MultiTrackerSyncOrchestrator",
    "MultiTrackerSyncResult",
    "OperationRecord",
    "ProgressCallback",
    "ProgressReporter",
    "ProgressState",
    "ProgressSyncPhase",
    "PullChanges",
    "PullResult",
    "ResolutionStrategy",
    "RestoreOperation",
    "RestoreResult",
    "ReverseSyncOrchestrator",
    "RollbackResult",
    "SmartMergeResolver",
    "SnapshotStore",
    "SourceFileUpdater",
    "SourceUpdateResult",
    "StateStore",
    "StoryDelta",
    "StoryFingerprint",
    "StorySnapshot",
    "SubtaskTrackerInfo",
    "SyncOrchestrator",
    "SyncPhase",
    "SyncResult",
    "SyncSnapshot",
    "SyncState",
    "SyncStatus",
    "SyncStrategy",
    "SyncableField",
    "ThreeWayMerger",
    "TrackerInfo",
    "TrackerSyncStatus",
    "TrackerTarget",
    "TrackerType",
    "TransactionManager",
    "TransactionOperationType",
    "TransactionResult",
    "TransactionState",
    "TransactionalSync",
    "check_idempotency",
    "compare_backup_to_current",
    "compute_content_hash",
    "compute_story_content_hash",
    "compute_story_hash",
    "create_audit_trail",
    "create_delta_tracker",
    "create_multi_tracker_orchestrator",
    "create_pre_sync_backup",
    "create_progress_reporter",
    "create_snapshot_from_sync",
    "create_transactional_sync",
    "detect_sync_conflicts",
    "is_content_unchanged",
    "resolve_conflict_with_merge",
    "restore_from_backup",
    "stories_differ",
]

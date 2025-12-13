"""
Sync Module - Orchestration of synchronization between markdown and issue tracker.
"""

from .orchestrator import SyncOrchestrator, SyncResult, FailedOperation
from .state import SyncState, StateStore, SyncPhase, OperationRecord
from .audit import AuditTrail, AuditEntry, AuditTrailRecorder, create_audit_trail
from .backup import (
    Backup,
    BackupManager,
    IssueSnapshot,
    RestoreResult,
    RestoreOperation,
    create_pre_sync_backup,
    restore_from_backup,
)
from .diff import (
    DiffResult,
    DiffCalculator,
    DiffFormatter,
    IssueDiff,
    FieldDiff,
    compare_backup_to_current,
)
from .reverse_sync import (
    ReverseSyncOrchestrator,
    PullResult,
    PullChanges,
    ChangeDetail,
)
from .conflict import (
    ConflictType,
    ResolutionStrategy,
    Conflict,
    ConflictReport,
    ConflictResolution,
    ConflictDetector,
    ConflictResolver,
    SyncSnapshot,
    StorySnapshot,
    FieldSnapshot,
    SnapshotStore,
    create_snapshot_from_sync,
)
from .multi_epic import (
    MultiEpicSyncOrchestrator,
    MultiEpicSyncResult,
    EpicSyncResult,
)
from .links import (
    LinkSyncOrchestrator,
    LinkSyncResult,
    LinkChange,
)
from .incremental import (
    StoryFingerprint,
    ChangeDetectionResult,
    ChangeTracker,
    IncrementalSyncStats,
    compute_story_hash,
    stories_differ,
)

# Parallel operations (optional, requires aiohttp)
try:
    from .parallel import (  # noqa: F401
        ParallelSyncOperations,
        ParallelSyncResult,
        is_parallel_available,
    )
    PARALLEL_AVAILABLE = True
except ImportError:
    PARALLEL_AVAILABLE = False

__all__ = [
    "SyncOrchestrator",
    "SyncResult",
    "FailedOperation",
    "SyncState",
    "StateStore",
    "SyncPhase",
    "OperationRecord",
    # Audit trail
    "AuditTrail",
    "AuditEntry",
    "AuditTrailRecorder",
    "create_audit_trail",
    # Backup & Restore
    "Backup",
    "BackupManager",
    "IssueSnapshot",
    "RestoreResult",
    "RestoreOperation",
    "create_pre_sync_backup",
    "restore_from_backup",
    # Diff
    "DiffResult",
    "DiffCalculator",
    "DiffFormatter",
    "IssueDiff",
    "FieldDiff",
    "compare_backup_to_current",
    # Reverse Sync (Pull)
    "ReverseSyncOrchestrator",
    "PullResult",
    "PullChanges",
    "ChangeDetail",
    # Conflict Detection
    "ConflictType",
    "ResolutionStrategy",
    "Conflict",
    "ConflictReport",
    "ConflictResolution",
    "ConflictDetector",
    "ConflictResolver",
    "SyncSnapshot",
    "StorySnapshot",
    "FieldSnapshot",
    "SnapshotStore",
    "create_snapshot_from_sync",
    # Multi-Epic Sync
    "MultiEpicSyncOrchestrator",
    "MultiEpicSyncResult",
    "EpicSyncResult",
    # Link Sync
    "LinkSyncOrchestrator",
    "LinkSyncResult",
    "LinkChange",
    # Incremental Sync
    "StoryFingerprint",
    "ChangeDetectionResult",
    "ChangeTracker",
    "IncrementalSyncStats",
    "compute_story_hash",
    "stories_differ",
    # Parallel Operations
    "PARALLEL_AVAILABLE",
]


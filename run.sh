#!/bin/bash
# Jira Markdown Sync Tool - Helper Script
#
# This script provides convenient shortcuts for common operations.
#
# Usage:
#   ./run.sh <command> [options]
#
# Commands:
#   export      Export current Jira state
#   analyze     Analyze differences (dry-run)
#   sync        Sync all changes (with confirmations)
#   sync-fast   Sync all changes (no confirmations)
#   validate    Validate sync is correct
#   fix-desc    Fix description formatting
#   sync-status Sync subtask statuses

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/md2jira.py"

# Default epic and markdown path (customize these)
DEFAULT_EPIC="${JIRA_EPIC:-}"
DEFAULT_MARKDOWN="${JIRA_MARKDOWN:-}"

# Parse arguments
COMMAND="${1:-help}"
shift || true

show_help() {
    echo "Jira Markdown Sync Tool"
    echo ""
    echo "Usage: ./run.sh <command> [--epic EPIC] [--markdown FILE] [options]"
    echo ""
    echo "Commands:"
    echo "  export       Export current Jira state to JSON"
    echo "  analyze      Analyze differences (dry-run)"
    echo "  sync         Sync all changes (with confirmations)"
    echo "  sync-fast    Sync all changes (no confirmations)"
    echo "  validate     Validate sync is correct"
    echo "  fix-desc     Fix description formatting"
    echo "  sync-status  Sync subtask statuses"
    echo "  help         Show this help message"
    echo ""
    echo "Options:"
    echo "  --epic, -e      Jira epic key (e.g., PROJ-123)"
    echo "  --markdown, -m  Path to markdown file"
    echo "  --story         Process only a specific story"
    echo "  --verbose, -v   Enable verbose logging"
    echo ""
    echo "Environment Variables:"
    echo "  JIRA_EPIC       Default epic key"
    echo "  JIRA_MARKDOWN   Default markdown file path"
    echo ""
    echo "Examples:"
    echo "  ./run.sh export --epic PROJ-123"
    echo "  ./run.sh analyze --markdown epic.md --epic PROJ-123"
    echo "  ./run.sh sync --markdown epic.md --epic PROJ-123"
    echo "  ./run.sh fix-desc --markdown epic.md --epic PROJ-123 --story US-001"
}

case "$COMMAND" in
    export)
        python3 "$PYTHON_SCRIPT" --export "$@"
        ;;
    analyze)
        python3 "$PYTHON_SCRIPT" --analyze-only "$@"
        ;;
    sync)
        python3 "$PYTHON_SCRIPT" --execute "$@"
        ;;
    sync-fast)
        python3 "$PYTHON_SCRIPT" --execute --no-confirm "$@"
        ;;
    validate)
        python3 "$PYTHON_SCRIPT" --validate "$@"
        ;;
    fix-desc)
        python3 "$PYTHON_SCRIPT" --fix-descriptions --execute --no-confirm "$@"
        ;;
    sync-status)
        python3 "$PYTHON_SCRIPT" --sync-status --execute --no-confirm "$@"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Run './run.sh help' for usage"
        exit 1
        ;;
esac

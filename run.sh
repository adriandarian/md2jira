#!/bin/bash
# md2jira - Quick runner script
# 
# Usage:
#   ./run.sh EPIC.md PROJ-123           # Dry-run
#   ./run.sh EPIC.md PROJ-123 --execute # Execute

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv if exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Check if installed
if ! python -c "import md2jira" 2>/dev/null; then
    echo "Installing md2jira..."
    pip install -e . -q
fi

# Run with arguments
python -m md2jira.cli.app "$@"

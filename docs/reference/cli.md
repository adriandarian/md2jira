# CLI Reference

Complete reference for all spectra command-line options.

## Synopsis

```bash
spectra [OPTIONS]
```

## Required Options

| Option | Short | Description |
|--------|-------|-------------|
| `--markdown PATH` | `-m` | Path to markdown file |
| `--epic KEY` | `-e` | Jira epic key (e.g., PROJ-123) |

## Common Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--execute` | `-x` | Execute changes (vs dry-run) | `false` |
| `--no-confirm` | | Skip confirmation prompts | `false` |
| `--verbose` | `-v` | Enable verbose output | `false` |
| `--quiet` | `-q` | Suppress non-essential output | `false` |
| `--help` | `-h` | Show help message | |
| `--version` | | Show version | |

## Sync Options

| Option | Description | Values |
|--------|-------------|--------|
| `--phase PHASE` | Run specific sync phase | `all`, `descriptions`, `subtasks`, `comments`, `statuses` |
| `--story ID` | Filter to specific story | Story ID (e.g., `STORY-001`, `PROJ-123`) |
| `--update-source` | Write tracker info back to source markdown file | `false` (default) |
| `--incremental` | Only sync changed stories (skip unchanged) | `false` (default) |

## Configuration Options

| Option | Description |
|--------|-------------|
| `--config PATH` | Path to config file |
| `--jira-url URL` | Override Jira URL |
| `--project KEY` | Override project key |

## Output Options

| Option | Description |
|--------|-------------|
| `--output FORMAT` | Output format: `text`, `json` |
| `--export PATH` | Export results to JSON file |
| `--no-color` | Disable colored output |
| `--log-file PATH` | Write logs to file |
| `--log-format FORMAT` | Log format: `text`, `json` |
| `--audit-trail PATH` | Export audit trail to JSON |

## Validation Options

| Option | Description |
|--------|-------------|
| `--validate` | Validate markdown only (no sync) |

## AI Fix Options

| Option | Description |
|--------|-------------|
| `--show-guide` | Display the spectra markdown format guide |
| `--suggest-fix` | Generate AI prompt for copy-paste fixing |
| `--auto-fix` | Automatically fix using AI CLI tool |
| `--ai-tool TOOL` | Specify AI tool for auto-fix (claude, ollama, aider, llm, mods, sgpt) |
| `--list-ai-tools` | List detected AI CLI tools available for auto-fix |

See [AI Fix Guide](/guide/ai-fix) for detailed usage.

## Interactive Mode

| Option | Description |
|--------|-------------|
| `--interactive` | `-i` | Step-by-step guided sync |
| `--resume` | Resume interrupted sync |

## Backup & Recovery

| Option | Description |
|--------|-------------|
| `--no-backup` | Disable automatic backup |
| `--list-backups` | List available backups |
| `--diff-backup ID` | Show diff from backup |
| `--diff-latest` | Show diff from latest backup |
| `--restore-backup ID` | Restore from backup |
| `--rollback` | Rollback last sync |

## Shell Completions

| Option | Description |
|--------|-------------|
| `--completions SHELL` | Output completion script | `bash`, `zsh`, `fish` |

## Examples

### Basic Sync

```bash
# Preview changes (dry-run)
spectra --markdown EPIC.md --epic PROJ-123

# Execute sync
spectra --markdown EPIC.md --epic PROJ-123 --execute

# Short form
spectra -m EPIC.md -e PROJ-123 -x
```

### Sync Specific Phases

```bash
# Sync descriptions only
spectra -m EPIC.md -e PROJ-123 -x --phase descriptions

# Sync subtasks only
spectra -m EPIC.md -e PROJ-123 -x --phase subtasks

# Sync comments only
spectra -m EPIC.md -e PROJ-123 -x --phase comments

# Sync status transitions only
spectra -m EPIC.md -e PROJ-123 -x --phase statuses
```

### Filter by Story

```bash
# Sync specific story
spectra -m EPIC.md -e PROJ-123 -x --story STORY-001

# Multiple stories (run multiple times)
spectra -m EPIC.md -e PROJ-123 -x --story STORY-001
spectra -m EPIC.md -e PROJ-123 -x --story STORY-002
```

### CI/CD Usage

```bash
# No prompts, JSON output
spectra -m EPIC.md -e PROJ-123 -x --no-confirm --output json

# Export results for processing
spectra -m EPIC.md -e PROJ-123 -x --no-confirm --export results.json

# Quiet mode (errors only)
spectra -m EPIC.md -e PROJ-123 -x --no-confirm -q
```

### Logging & Debugging

```bash
# Verbose output
spectra -m EPIC.md -e PROJ-123 -v

# Write logs to file
spectra -m EPIC.md -e PROJ-123 -x --log-file sync.log

# JSON logs (for log aggregation)
spectra -m EPIC.md -e PROJ-123 -x --log-format json

# Full audit trail
spectra -m EPIC.md -e PROJ-123 -x --audit-trail audit.json
```

### Backup & Recovery

```bash
# List backups
spectra --list-backups

# View diff from latest backup
spectra --diff-latest --epic PROJ-123

# View diff from specific backup
spectra --diff-backup backup_20250113_120000 --epic PROJ-123

# Restore from backup (dry-run)
spectra --restore-backup backup_20250113_120000 --epic PROJ-123

# Restore from backup (execute)
spectra --restore-backup backup_20250113_120000 --epic PROJ-123 --execute

# Rollback last sync
spectra --rollback --epic PROJ-123 --execute
```

### Interactive Mode

```bash
# Guided sync with previews
spectra -m EPIC.md -e PROJ-123 --interactive

# Resume interrupted sync
spectra -m EPIC.md -e PROJ-123 --resume
```

### Source File Update (Tracker Writeback)

```bash
# Sync and write tracker info back to markdown file
spectra -m EPIC.md -e PROJ-123 -x --update-source

# After sync, your markdown will contain:
# > **Tracker:** Jira
# > **Issue:** [PROJ-456](https://company.atlassian.net/browse/PROJ-456)
# > **Last Synced:** 2025-01-15 14:30 UTC
# > **Sync Status:** ✅ Synced
# > **Content Hash:** `a1b2c3d4`
```

### Validation

```bash
# Validate markdown format only
spectra --validate --markdown EPIC.md

# Validate with epic context
spectra --validate --markdown EPIC.md --epic PROJ-123
```

### AI Fix

```bash
# View the format guide
spectra --validate --markdown EPIC.md --show-guide

# Get AI prompt for copy-paste
spectra --validate --markdown EPIC.md --suggest-fix

# Auto-fix interactively (select AI tool)
spectra --validate --markdown EPIC.md --auto-fix

# Auto-fix with specific AI tool
spectra --validate --markdown EPIC.md --auto-fix --ai-tool claude

# List available AI tools
spectra --list-ai-tools
```

See [AI Fix Guide](/guide/ai-fix) for detailed usage and troubleshooting.

### Configuration

```bash
# Use specific config file
spectra -m EPIC.md -e PROJ-123 --config ~/.spectra-prod.yaml

# Override Jira URL
spectra -m EPIC.md -e PROJ-123 --jira-url https://other.atlassian.net

# Override project
spectra -m EPIC.md -e PROJ-123 --project OTHER
```

## Exit Codes

See [Exit Codes Reference](/reference/exit-codes) for detailed exit code documentation.

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | File not found |
| 4 | Connection error |
| 5 | Authentication error |
| 6 | Validation error |
| 64 | Partial success |
| 80 | Cancelled by user |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `JIRA_URL` | Jira instance URL |
| `JIRA_EMAIL` | Jira account email |
| `JIRA_API_TOKEN` | Jira API token |
| `JIRA_PROJECT` | Default project key |
| `SPECTRA_VERBOSE` | Enable verbose output |
| `SPECTRA_NO_COLOR` | Disable colored output |

See [Environment Variables](/guide/environment) for complete documentation.


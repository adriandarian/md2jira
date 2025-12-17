# spectra

<div align="center">

[![CI](https://github.com/adriandarian/spectra/actions/workflows/pr.yml/badge.svg)](https://github.com/adriandarian/spectra/actions/workflows/pr.yml)
[![Release](https://github.com/adriandarian/spectra/actions/workflows/release.yml/badge.svg)](https://github.com/adriandarian/spectra/actions/workflows/release.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**A production-grade CLI tool for synchronizing markdown specifications with issue trackers**

*Supports Jira, GitHub Issues, Azure DevOps, Linear, and more*

[Features](#features) •
[Installation](#installation) •
[Quick Start](#quick-start) •
[Architecture](#architecture) •
[Documentation](#documentation)

</div>

---

## Features

🚀 **Multi-Platform Sync** - Sync to Jira, GitHub Issues, Azure DevOps, Linear, and Confluence

📝 **Markdown & YAML Native** - Write specs in markdown or YAML, sync to any issue tracker

🔄 **Smart Matching** - Fuzzy title matching between specs and existing issues

🛡️ **Safe by Default** - Dry-run mode, confirmations, and detailed previews before any changes

⚡ **Command Pattern** - Undo-capable operations with full audit trail

🔌 **Plugin System** - Extensible architecture for custom parsers, trackers, and formatters

📊 **Rich Output** - Beautiful CLI with progress bars, colored output, and detailed reports

🔗 **Bi-directional Sync** - Pull changes back from trackers to update local specs

## Installation

### Quick Install

```bash
# pip (all platforms)
pip install spectra

# pipx (isolated environment)
pipx install spectra

# Homebrew (macOS/Linux)
brew install adriandarian/spectra/spectra

# Chocolatey (Windows)
choco install spectra

# Universal Linux installer
curl -fsSL https://raw.githubusercontent.com/adriandarian/spectra/main/dist/packages/linux/install.sh | bash
```

### From Source

```bash
git clone https://github.com/adriandarian/spectra.git
cd spectra
pip install -e ".[dev]"
```

### Docker

```bash
# Pull the image (when available on Docker Hub)
docker pull adriandarian/spectra:latest

# Or build locally
docker build -t spectra:latest -f dist/docker/Dockerfile .

# Run with your markdown file and Jira credentials
docker run --rm \
  -e JIRA_URL=https://your-company.atlassian.net \
  -e JIRA_EMAIL=your.email@company.com \
  -e JIRA_API_TOKEN=your-api-token \
  -v $(pwd):/workspace \
  spectra:latest \
  --markdown EPIC.md --epic PROJ-123

# Execute sync (not just dry-run)
docker run --rm \
  -e JIRA_URL=https://your-company.atlassian.net \
  -e JIRA_EMAIL=your.email@company.com \
  -e JIRA_API_TOKEN=your-api-token \
  -v $(pwd):/workspace \
  spectra:latest \
  --markdown EPIC.md --epic PROJ-123 --execute
```

### Docker Compose

For easier usage with persistent configuration:

```bash
# 1. Copy the example environment file
cp .env.example .env

# 2. Edit .env with your Jira credentials
#    JIRA_URL=https://your-company.atlassian.net
#    JIRA_EMAIL=your.email@company.com
#    JIRA_API_TOKEN=your-api-token

# 3. Run a dry-run preview
docker compose run --rm spectra --markdown EPIC.md --epic PROJ-123

# 4. Execute the sync
docker compose run --rm spectra --markdown EPIC.md --epic PROJ-123 --execute
```

## Quick Start

### 1. Set up environment variables

Create a `.env` file:

```bash
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your.email@company.com
JIRA_API_TOKEN=your-api-token
```

### 2. Create your markdown epic

```markdown
### ✅ US-001: User Authentication

| Field | Value |
|-------|-------|
| **Story Points** | 5 |
| **Priority** | 🟡 High |
| **Status** | ✅ Done |

#### Description

**As a** user
**I want** to authenticate securely
**So that** my data is protected

#### Subtasks

| # | Subtask | Description | SP | Status |
|---|---------|-------------|----|---------| 
| 1 | Create login form | Build the login UI | 2 | ✅ Done |
| 2 | Implement JWT auth | Add JWT token handling | 3 | ✅ Done |
```

### 3. Sync to Jira

```bash
# Preview changes (dry-run)
spectra --markdown EPIC.md --epic PROJ-123

# Execute sync
spectra --markdown EPIC.md --epic PROJ-123 --execute

# Sync specific phase only
spectra --markdown EPIC.md --epic PROJ-123 --execute --phase descriptions
```

## Architecture

spectra follows a **Clean Architecture** / **Hexagonal Architecture** pattern for maximum flexibility and testability.

```
src/spectra/
├── core/                     # Pure domain logic (no external deps)
│   ├── domain/               # Entities, value objects, enums
│   │   ├── entities.py       # Epic, UserStory, Subtask, Comment
│   │   ├── value_objects.py  # StoryId, IssueKey, Description
│   │   ├── enums.py          # Status, Priority, IssueType
│   │   └── events.py         # Domain events for audit trail
│   └── ports/                # Abstract interfaces
│       ├── issue_tracker.py  # IssueTrackerPort interface
│       ├── document_parser.py
│       └── document_formatter.py
├── adapters/                 # Infrastructure implementations
│   ├── jira/                 # Jira API adapter
│   │   ├── adapter.py        # IssueTrackerPort implementation
│   │   └── client.py         # Low-level HTTP client
│   ├── parsers/              # Document parsers
│   │   └── markdown.py       # Markdown parser
│   ├── formatters/           # Output formatters
│   │   └── adf.py            # Atlassian Document Format
│   └── config/               # Configuration providers
│       └── environment.py    # Env vars / .env loader
├── application/              # Use cases / orchestration
│   ├── commands/             # Command pattern handlers
│   │   ├── base.py           # Command, CommandResult, CommandBatch
│   │   └── issue_commands.py # UpdateDescription, CreateSubtask, etc.
│   └── sync/                 # Sync orchestrator
│       └── orchestrator.py   # Main sync logic
├── cli/                      # Command line interface
│   ├── app.py                # Entry point, argument parsing
│   └── output.py             # Rich console output
└── plugins/                  # Extension system
    ├── base.py               # Plugin base classes
    ├── hooks.py              # Hook system for extensibility
    └── registry.py           # Plugin discovery and loading
```

### Key Patterns

- **Ports & Adapters**: Core logic depends only on abstract interfaces (ports), making it easy to swap implementations
- **Command Pattern**: All write operations are encapsulated as commands, enabling undo/redo and audit trails
- **Event-Driven**: Domain events provide loose coupling and enable audit logging
- **Plugin System**: Extend functionality without modifying core code

### Adding a New Tracker (e.g., GitHub Issues)

```python
from spectra.core.ports import IssueTrackerPort

class GitHubAdapter(IssueTrackerPort):
    @property
    def name(self) -> str:
        return "GitHub"
    
    def get_epic_children(self, epic_key: str) -> list[IssueData]:
        # Implement GitHub API calls
        ...
```

### Using Hooks

```python
from spectra.plugins import HookPoint, get_registry

hook_manager = get_registry().hook_manager

@hook_manager.hook(HookPoint.BEFORE_SYNC)
def log_sync_start(ctx):
    print(f"Starting sync for epic: {ctx.data['epic_key']}")

@hook_manager.hook(HookPoint.ON_ERROR)
def handle_errors(ctx):
    send_slack_notification(ctx.error)
```

## CLI Reference

```bash
spectra --help
```

### Common Options

| Option | Description |
|--------|-------------|
| `--markdown, -m` | Path to markdown file (required) |
| `--epic, -e` | Jira epic key (required) |
| `--execute, -x` | Execute changes (default: dry-run) |
| `--no-confirm` | Skip confirmation prompts |
| `--phase` | Run specific phase: `all`, `descriptions`, `subtasks`, `comments`, `statuses` |
| `--story` | Filter to specific story ID |
| `--verbose, -v` | Verbose output |
| `--export` | Export results to JSON |
| `--validate` | Validate markdown only |

### Examples

```bash
# Validate markdown format
spectra -m EPIC.md -e PROJ-123 --validate

# Preview all changes
spectra -m EPIC.md -e PROJ-123 -v

# Sync descriptions only
spectra -m EPIC.md -e PROJ-123 -x --phase descriptions

# Full sync without prompts
spectra -m EPIC.md -e PROJ-123 -x --no-confirm

# Export results
spectra -m EPIC.md -e PROJ-123 -x --export sync-results.json
```

## Documentation

Visit our **[documentation site](docs/index.md)** for comprehensive guides:

- [Getting Started](docs/guide/getting-started.md) - Quick start guide
- [Installation](docs/guide/installation.md) - All installation options
- [Configuration](docs/guide/configuration.md) - Configuration file format and options
- [CLI Reference](docs/reference/cli.md) - Complete CLI documentation
- [Architecture](docs/guide/architecture.md) - System architecture overview
- [Plugins](docs/guide/plugins.md) - Plugin development guide

## Development

### Setup

```bash
# Clone and install
git clone https://github.com/adriandarian/spectra.git
cd spectra
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src/spectra

# Type checking
mypy src/

# Linting
ruff check src/ tests/

# Formatting
ruff format src/ tests/
```

### Project Structure

```
spectra/
├── src/spectra/      # Python source code
├── tests/            # Test suite
├── docs/             # Documentation (VitePress)
├── integrations/     # Editor & platform integrations
│   ├── github-action/
│   ├── vscode/
│   ├── neovim/
│   └── terraform/
├── dist/             # Distribution files
│   ├── docker/
│   ├── completions/
│   └── packages/
├── scripts/          # Development scripts
└── pyproject.toml    # Project config
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a PR

---

<div align="center">
Made with ❤️ by <a href="https://github.com/adriandarian">Adrian Darian</a>
</div>

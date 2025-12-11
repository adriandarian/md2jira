# md2jira

A CLI tool for synchronizing markdown documentation with Jira. Sync user stories, subtasks, descriptions, comments, and statuses from markdown files to Jira epics.

## Documentation

| Document | Description |
|----------|-------------|
| [SCHEMA.md](docs/SCHEMA.md) | Complete markdown format specification |
| [TEMPLATE.md](docs/TEMPLATE.md) | Blank template to start your epic |
| [EXAMPLE.md](docs/EXAMPLE.md) | Full working example (e-commerce) |
| [AI_PROMPT.md](docs/AI_PROMPT.md) | Prompts for AI-assisted generation |

## Features

- 🔒 **Dry-run mode** by default (use `--execute` to make changes)
- ✅ **Confirmation prompts** before each write operation
- 📋 **Detailed logging** of all actions
- 💾 **Export current state** for backup before modifications
- 📝 **Markdown to ADF conversion** with proper formatting (bold, checkboxes, code)
- 📊 **Subtask management** with descriptions, assignees, and story points
- 💬 **Commit comments** as formatted tables
- 🔄 **Status synchronization** based on markdown

## Installation

```bash
# Clone the repo
git clone https://github.com/adriandarian/md2jira.git
cd md2jira

# Install dependencies
pip install -r requirements.txt
```

## Setup

### Configure Jira Credentials

Create a `.env` file in the project directory:

```bash
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token
```

Get your API token from: https://id.atlassian.com/manage-profile/security/api-tokens

## Quick Start

```bash
# Analyze differences (dry-run, safe)
python md2jira.py --markdown /path/to/epic.md --epic PROJ-123

# Export current Jira state to JSON backup
python md2jira.py --epic PROJ-123 --export

# Sync with confirmations
python md2jira.py --markdown epic.md --epic PROJ-123 --execute

# Sync without confirmations
python md2jira.py --markdown epic.md --epic PROJ-123 --execute --no-confirm
```

## Usage

### Basic Commands

```bash
# Analyze only (see what would change)
python md2jira.py --markdown epic.md --epic PROJ-123 --analyze-only

# Validate sync is correct
python md2jira.py --markdown epic.md --epic PROJ-123 --validate

# Fix description formatting
python md2jira.py --markdown epic.md --epic PROJ-123 --fix-descriptions --execute

# Sync subtask statuses
python md2jira.py --markdown epic.md --epic PROJ-123 --sync-status --execute

# Process only a specific story
python md2jira.py --markdown epic.md --epic PROJ-123 --story US-001 --execute
```

### Phased Sync

Run specific phases individually for more control:

```bash
# Phase 1: Sync descriptions only
python md2jira.py --markdown epic.md --epic PROJ-123 --execute --phase 1 --no-confirm

# Phase 2: Create subtasks only
python md2jira.py --markdown epic.md --epic PROJ-123 --execute --phase 2 --no-confirm

# Phase 3: Add commit comments only
python md2jira.py --markdown epic.md --epic PROJ-123 --execute --phase 3 --no-confirm
```

### Helper Script

Use `run.sh` for common operations:

```bash
./run.sh export --epic PROJ-123
./run.sh analyze --markdown epic.md --epic PROJ-123
./run.sh sync --markdown epic.md --epic PROJ-123
./run.sh fix-desc --markdown epic.md --epic PROJ-123
./run.sh sync-status --markdown epic.md --epic PROJ-123
./run.sh validate --markdown epic.md --epic PROJ-123
```

## Expected Markdown Format

The parser expects user stories in this format:

```markdown
### 🔧 US-001: Story Title

| Field | Value |
|-------|-------|
| **Story Points** | 5 |
| **Priority** | 🟡 High |
| **Status** | ✅ Done |

#### Description
**As a** developer
**I want** feature X
**So that** I can achieve Y

#### Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [x] Completed criterion

#### Subtasks
| # | Subtask | Description | SP | Status |
|---|---------|-------------|-----|--------|
| 1 | Setup | Initial setup | 1 | ✅ Done |
| 2 | Implement | Core implementation | 3 | 🔄 In Progress |

#### Related Commits
| Commit | Message |
|--------|---------|
| `abc1234` | feat: add feature X |
| `def5678` | fix: resolve issue Y |
```

## CLI Reference

| Option | Description |
|--------|-------------|
| `--markdown, -m` | Path to markdown file with user stories |
| `--epic, -e` | Jira epic key (e.g., PROJ-123) |
| `--project, -p` | Jira project key (defaults to epic prefix) |
| `--jira-url` | Jira instance URL (or set JIRA_URL env var) |
| `--export` | Export current Jira state to JSON |
| `--execute` | Actually make changes (default is dry-run) |
| `--no-confirm` | Skip confirmation prompts |
| `--verbose, -v` | Enable verbose logging |
| `--analyze-only` | Only analyze, don't sync |
| `--phase N` | Run only phase 1, 2, or 3 |
| `--validate` | Validate stories are correctly synced |
| `--fix-descriptions` | Re-sync descriptions with proper formatting |
| `--sync-status` | Sync subtask statuses from markdown |
| `--story` | Process only a specific story |

## Customization

### Story Pattern

The default pattern for detecting user stories is:

```regex
### [^\n]+ (US-\d+): ([^\n]+)\n
```

To customize, modify `STORY_PATTERN` in the `MarkdownEpicParser` class.

### Story Points Field

Jira uses custom fields for story points. The default is:

```python
STORY_POINTS_FIELD = "customfield_10014"
```

Update in `JiraClient` if your Jira uses a different field.

### Workflow Transitions

The default transitions are configured for a typical Jira workflow:

```
Analyze → Open → In Progress → Resolved
```

Modify `TRANSITIONS` in `JiraClient` if your workflow differs.

## Safety Features

1. **Dry-run by default** - No changes unless `--execute` is specified
2. **Confirmations** - Each change requires approval (unless `--no-confirm`)
3. **Export** - Create backups before modifying
4. **Phased execution** - Run sync in stages
5. **Story filter** - Test on a single story first

## Recommended Workflow

```bash
# 1. Export current state as backup
python md2jira.py --epic PROJ-123 --export

# 2. Analyze differences
python md2jira.py --markdown epic.md --epic PROJ-123 --analyze-only

# 3. Dry-run to see what would change
python md2jira.py --markdown epic.md --epic PROJ-123

# 4. Execute with confirmations
python md2jira.py --markdown epic.md --epic PROJ-123 --execute

# 5. Validate sync
python md2jira.py --markdown epic.md --epic PROJ-123 --validate
```

## Creating Your Epic Markdown

### Option 1: Use the Template

Copy [docs/TEMPLATE.md](docs/TEMPLATE.md) and fill in your stories.

### Option 2: Use AI Generation

Use the prompts in [docs/AI_PROMPT.md](docs/AI_PROMPT.md) with Claude, ChatGPT, or other AI assistants to generate a complete epic document.

### Option 3: Follow the Schema

Read [docs/SCHEMA.md](docs/SCHEMA.md) for the complete format specification and create your own.

### Quick Format Reference

```markdown
### 🔧 US-XXX: Story Title       ← Required format

| Field | Value |                 ← Required table
| **Story Points** | N |
| **Priority** | 🟡 High |
| **Status** | 📋 Planned |

#### Description                  ← Required section
**As a** [role]
**I want** [feature]
**So that** [benefit]

#### Acceptance Criteria          ← Optional
- [ ] Criterion

#### Subtasks                     ← Optional
| # | Subtask | Description | SP | Status |

#### Related Commits              ← Optional
| Commit | Message |
| `hash` | message |
```

## License

MIT


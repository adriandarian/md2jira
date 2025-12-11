# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Nothing yet

### Changed
- Nothing yet

### Deprecated
- Nothing yet

### Removed
- Nothing yet

### Fixed
- Nothing yet

### Security
- Nothing yet

## [2.0.0] - 2024-12-11

### Added
- **Hexagonal Architecture**: Complete restructure following ports and adapters pattern
- **Plugin System**: Extensible architecture with hook-based plugin support
  - Plugin registry with entry point discovery
  - Lifecycle hooks for customization (pre/post sync, validation, etc.)
- **Domain-Driven Design**: Rich domain model with entities, value objects, and events
  - `Epic`, `Story`, `Task` entities with full lifecycle management
  - `IssueKey`, `StoryPoints`, `Markdown` value objects for type safety
  - Domain events for tracking operations (`IssueCreated`, `IssueUpdated`, etc.)
- **Command Pattern**: Application layer with command handlers
  - `CreateIssueCommand`, `UpdateIssueCommand`, `DeleteIssueCommand`
  - Sync orchestrator for coordinating operations
- **Port Interfaces**: Clean abstractions for external dependencies
  - `IssueTracker` port for Jira/GitHub/Linear adapters
  - `DocumentParser` port for markdown/YAML parsers
  - `DocumentFormatter` port for ADF/HTML formatters
  - `ConfigProvider` port for environment/file configuration
- **Atlassian Document Format (ADF)**: Full support for Jira Cloud's rich text format
  - Headings, paragraphs, lists, code blocks
  - Bold, italic, strikethrough, code formatting
  - Links, horizontal rules, blockquotes
- **Documentation**: Comprehensive docs in `docs/` directory
  - `AI_PROMPT.md` - AI assistant integration guide
  - `EXAMPLE.md` - Example markdown document
  - `SCHEMA.md` - Markdown format specification
  - `TEMPLATE.md` - Template for creating epics
- **Improvements Roadmap**: `IMPROVEMENTS.md` tracking all planned features

### Changed
- Project restructured from flat module to `src/` layout
- CLI moved to dedicated `cli/` package with Typer-based interface
- Configuration now uses environment-based adapter with validation
- All public APIs have complete type annotations

### Removed
- Legacy flat module structure
- Direct Jira API calls (now abstracted behind ports)

## [1.0.0] - 2024-12-10

### Added
- Initial release of md2jira
- **Markdown Parser**: Parse structured markdown documents into Jira issues
  - Epic, Story, and Task hierarchy support
  - Story points extraction
  - Acceptance criteria parsing
  - Description with markdown formatting
- **Jira Integration**: Sync parsed issues to Jira Cloud
  - Create epics, stories, and tasks
  - Update existing issues via Jira key references
  - Link stories to epics
  - Link tasks to stories
- **CLI Interface**: Command-line tool for syncing
  - `sync` command for full synchronization
  - `validate` command for markdown validation
  - `--dry-run` flag for preview mode
  - Rich console output with progress indicators
- **Configuration**: Environment variable configuration
  - `JIRA_URL` - Jira instance URL
  - `JIRA_EMAIL` - User email for authentication
  - `JIRA_API_TOKEN` - API token for authentication
  - `JIRA_PROJECT_KEY` - Target project key
- **MIT License**: Open source under MIT license

[Unreleased]: https://github.com/adriandarian/md2jira/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/adriandarian/md2jira/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/adriandarian/md2jira/releases/tag/v1.0.0


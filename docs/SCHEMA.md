# md2jira Markdown Schema

This document defines the exact schema that md2jira parses. Follow this structure for successful Jira synchronization.

## Quick Reference

```
# Epic Title                           ← H1: Epic name
## User Stories                        ← H2: Stories section
### 🔧 US-XXX: Story Title             ← H3: Individual story (REQUIRED FORMAT)
| Field | Value |                      ← Metadata table
| **Story Points** | N |
| **Priority** | emoji Priority |
| **Status** | emoji Status |
#### Description                       ← H4: Description section
**As a** role
**I want** feature
**So that** benefit
#### Acceptance Criteria               ← H4: Acceptance criteria
- [ ] Criterion 1
#### Subtasks                          ← H4: Subtasks table
| # | Subtask | Description | SP | Status |
#### Related Commits                   ← H4: Commits table
| Commit | Message |
---                                    ← Story separator
```

## Detailed Schema

### Story Header (REQUIRED)

```markdown
### [emoji] US-XXX: [Title]
```

**Pattern**: `### [^\n]+ (US-\d+): ([^\n]+)\n`

**Examples**:
```markdown
### 🔧 US-001: Migrate to TypeScript
### 🚀 US-002: Add Authentication
### 🎨 US-003: Redesign Dashboard
### 🐛 US-004: Fix Login Bug
### 📚 US-005: Update Documentation
```

**Emoji Guide**:
| Emoji | Meaning |
|-------|---------|
| 🔧 | Technical/Infrastructure |
| 🚀 | New Feature |
| 🎨 | UI/Design |
| 🐛 | Bug Fix |
| 📚 | Documentation |
| 🔒 | Security |
| ⚡ | Performance |
| ♻️ | Refactoring |

---

### Metadata Table (REQUIRED)

```markdown
| Field | Value |
|-------|-------|
| **Story Points** | [number] |
| **Priority** | [emoji] [Priority] |
| **Status** | [emoji] [Status] |
```

**Story Points**: Integer (typically Fibonacci: 1, 2, 3, 5, 8, 13)

**Priority Values**:
| Value | Parsed As |
|-------|-----------|
| `🔴 Critical` | Critical |
| `🟡 High` | High |
| `🟢 Medium` | Medium |
| `🟢 Low` | Low |

**Status Values**:
| Value | Parsed As | Jira Status |
|-------|-----------|-------------|
| `✅ Done` | Done | Resolved |
| `🔄 In Progress` | In Progress | In Progress |
| `📋 Planned` | Planned | Open |

---

### Description Section (REQUIRED)

```markdown
#### Description

**As a** [role]
**I want** [feature]
**So that** [benefit]

[Optional additional context]
```

**Format Notes**:
- Must use `**As a**`, `**I want**`, `**So that**` with bold markers
- Each part should be on its own line
- Additional paragraphs after the three-part description are preserved

**Example**:
```markdown
#### Description

**As a** developer maintaining the codebase
**I want** automated code formatting on save
**So that** I can focus on logic instead of style

This feature will integrate with VS Code and other IDEs that support format-on-save.
```

---

### Acceptance Criteria Section (OPTIONAL)

```markdown
#### Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [x] Completed criterion
```

**Format Notes**:
- Use `- [ ]` for unchecked items
- Use `- [x]` for checked items (synced as checked in Jira)
- Each criterion on its own line

---

### Subtasks Table (OPTIONAL)

```markdown
#### Subtasks

| # | Subtask | Description | SP | Status |
|---|---------|-------------|:--:|--------|
| 1 | Task Name | Task description | 1 | ✅ Done |
| 2 | Task Name | Task description | 2 | 🔄 In Progress |
| 3 | Task Name | Task description | 1 | 📋 Planned |
```

**Columns**:
| Column | Description | Required |
|--------|-------------|----------|
| # | Sequential number | Yes |
| Subtask | Name (max 255 chars in Jira) | Yes |
| Description | Detailed description | Yes |
| SP | Story points (integer) | Yes |
| Status | Same as story status | Yes |

**Status Values for Subtasks**:
- `✅ Done` → Resolved
- `🔄 In Progress` → In Progress
- `📋 Planned` → Open

---

### Related Commits Section (OPTIONAL)

```markdown
#### Related Commits

| Commit | Message |
|--------|---------|
| `abc1234` | feat: add new feature |
| `def5678` | fix: resolve issue |
```

**Format Notes**:
- Commit hash must be wrapped in backticks: `` `hash` ``
- Short hash (7+ chars) is typical
- Message can be the full commit message or abbreviated

---

### Story Separator

```markdown
---
```

Use horizontal rules to separate stories for better readability.

---

## Complete Example

```markdown
# 🚀 Project Modernization Epic

> **Epic: Modernize legacy system to modern stack**

---

## Epic Summary

| Field | Value |
|-------|-------|
| **Epic Name** | Project Modernization |
| **Status** | 🔄 In Progress |
| **Priority** | 🔴 Critical |
| **Start Date** | January 2025 |
| **Target Release** | v2.0.0 |

### Summary

Modernize the legacy PHP application to a modern TypeScript/React stack.

---

## User Stories

---

### 🔧 US-001: Set Up TypeScript Configuration

| Field | Value |
|-------|-------|
| **Story Points** | 3 |
| **Priority** | 🔴 Critical |
| **Status** | ✅ Done |

#### Description

**As a** developer
**I want** TypeScript configured with strict mode
**So that** I catch type errors at compile time

#### Acceptance Criteria

- [ ] tsconfig.json created with strict mode
- [ ] All source files compile without errors
- [ ] IDE shows proper type hints

#### Subtasks

| # | Subtask | Description | SP | Status |
|---|---------|-------------|:--:|--------|
| 1 | Create tsconfig.json | Initialize TypeScript configuration | 1 | ✅ Done |
| 2 | Configure paths | Set up path aliases for imports | 1 | ✅ Done |
| 3 | Add build scripts | Create npm scripts for compilation | 1 | ✅ Done |

#### Related Commits

| Commit | Message |
|--------|---------|
| `a1b2c3d` | chore: initialize TypeScript configuration |
| `e4f5g6h` | feat: add path aliases |

---

### 🚀 US-002: Implement User Authentication

| Field | Value |
|-------|-------|
| **Story Points** | 8 |
| **Priority** | 🟡 High |
| **Status** | 🔄 In Progress |

#### Description

**As a** user
**I want** to log in with my credentials
**So that** I can access my personalized dashboard

#### Acceptance Criteria

- [ ] Login form validates input
- [ ] JWT tokens issued on successful login
- [ ] Refresh token rotation implemented
- [ ] Session persists across browser tabs

#### Subtasks

| # | Subtask | Description | SP | Status |
|---|---------|-------------|:--:|--------|
| 1 | Create login UI | Build login form with validation | 2 | ✅ Done |
| 2 | Implement JWT auth | Set up JWT generation and validation | 3 | 🔄 In Progress |
| 3 | Add refresh tokens | Implement token refresh flow | 2 | 📋 Planned |
| 4 | Session management | Handle multi-tab sessions | 1 | 📋 Planned |

---
```

## Validation Checklist

Before running md2jira, verify:

- [ ] Each story has `### [emoji] US-XXX: Title` format
- [ ] Each story has the metadata table with Story Points, Priority, Status
- [ ] Each story has `#### Description` with As a/I want/So that
- [ ] Subtasks table has all 5 columns: #, Subtask, Description, SP, Status
- [ ] Commits table uses backticks around commit hashes
- [ ] Stories are separated by `---`

## Common Parsing Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Story not detected | Missing `US-XXX:` pattern | Use exact format: `### 🔧 US-001: Title` |
| Missing description | Wrong heading level | Use `#### Description` (H4) |
| Subtasks not created | Wrong table format | Ensure 5 columns with correct headers |
| Status not synced | Wrong emoji | Use exact emojis: ✅ 🔄 📋 |


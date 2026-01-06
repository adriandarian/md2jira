# Spectra Helix Configuration

Helix editor configuration for Spectra markdown files with LSP support.

## Features

- **LSP Integration** - Full language server support via spectra-lsp
- **Syntax Highlighting** - Enhanced markdown highlighting for Spectra
- **Completions** - Auto-complete status, priority, and tracker IDs
- **Diagnostics** - Real-time validation errors
- **Go to Definition** - Navigate to story definitions
- **Hover** - View tracker issue details

## Installation

### 1. Install Spectra LSP

```bash
pip install spectra-lsp
```

### 2. Configure Helix

Add the following to your Helix configuration:

**`~/.config/helix/languages.toml`**:

```toml
# Add Spectra language server
[language-server.spectra-lsp]
command = "spectra-lsp"
args = ["--stdio"]

# Configure for Spectra markdown files
[[language]]
name = "spectra"
scope = "source.spectra"
injection-regex = "spectra"
file-types = [{ glob = "*.spectra.md" }]
roots = ["spectra.yaml", "spectra.toml", ".spectra"]
language-servers = ["spectra-lsp"]
indent = { tab-width = 2, unit = "  " }
grammar = "markdown"

# Also enable for regular markdown files
[[language]]
name = "markdown"
language-servers = ["marksman", "spectra-lsp"]
```

### 3. Copy Query Files (Optional)

For enhanced highlighting, copy the query files:

```bash
mkdir -p ~/.config/helix/runtime/queries/spectra
cp integrations/helix/queries/* ~/.config/helix/runtime/queries/spectra/
```

## Key Bindings

The default Helix LSP bindings work automatically:

| Action | Key |
|--------|-----|
| Go to definition | `gd` |
| Hover documentation | `K` |
| Code actions | `<space>a` |
| Show diagnostics | `<space>d` |
| Rename symbol | `<space>r` |
| Format document | `<space>f` |
| Completion | `<C-x><C-o>` or auto |

### Custom Key Bindings

Add to `~/.config/helix/config.toml`:

```toml
[keys.normal]
"<space>sv" = ":sh spectra --validate --markdown %"
"<space>ss" = ":sh spectra --sync --markdown %"
"<space>sp" = ":sh spectra plan --markdown %"

[keys.normal.space.s]
v = ":sh spectra --validate --markdown %"
s = ":sh spectra --sync --markdown %"
p = ":sh spectra plan --markdown %"
```

## LSP Settings

The LSP server can be configured with initialization options:

```toml
[language-server.spectra-lsp]
command = "spectra-lsp"
args = ["--stdio"]

[language-server.spectra-lsp.config]
spectra.tracker.type = "jira"
spectra.tracker.url = "https://your-org.atlassian.net"
spectra.tracker.projectKey = "PROJ"
spectra.validation.validateOnSave = true
spectra.validation.validateOnType = true
spectra.diagnostics.showWarnings = true
spectra.diagnostics.showHints = true
```

## Verification

After configuration, verify the setup:

1. Open a `.spectra.md` or `.md` file
2. Check `:log` for LSP connection messages
3. Type `**Status**: ` and check for completions
4. Press `K` on a story header for hover info
5. Check diagnostics with `<space>d`

## Troubleshooting

### LSP Not Starting

1. Verify `spectra-lsp` is in PATH:
   ```bash
   which spectra-lsp
   ```

2. Test the server directly:
   ```bash
   spectra-lsp --stdio
   ```

3. Check Helix logs:
   ```
   :log
   ```

### No Completions

Ensure the cursor is at the right position (after `**Status**: ` etc.)

### Diagnostics Not Showing

Check that `spectra` CLI is installed:
```bash
spectra --version
```

## File Structure

```
helix/
├── README.md
├── languages.toml          # Language configuration
├── config.toml             # Editor configuration
└── queries/
    └── spectra/
        ├── highlights.scm  # Syntax highlighting
        ├── injections.scm  # Language injections
        └── textobjects.scm # Text object definitions
```

## License

MIT - See [LICENSE](../../LICENSE)

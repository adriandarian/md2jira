# spectra.nvim

Neovim plugin for [spectra](https://github.com/your-org/spectra) - sync markdown documentation with Jira.

## ✨ Features

- 🔍 **Telescope Integration** - Fuzzy find stories and epics
- ✅ **Validate** - Check markdown syntax and structure
- 🔄 **Sync** - Push changes to Jira (dry-run or execute)
- 📊 **Dashboard** - View sync status at a glance
- ⌨️ **Keymaps** - Quick access to common operations
- 🔔 **Notifications** - Status updates via vim.notify

## 📦 Installation

### lazy.nvim

```lua
{
  "spectra/nvim-plugin",
  dependencies = {
    "nvim-telescope/telescope.nvim",  -- optional, for fuzzy finding
  },
  ft = "markdown",
  config = function()
    require("spectra").setup({})
  end,
}
```

### packer.nvim

```lua
use {
  "spectra/nvim-plugin",
  requires = { "nvim-telescope/telescope.nvim" },
  config = function()
    require("spectra").setup({})
  end,
}
```

## ⚙️ Configuration

```lua
require("spectra").setup({
  -- Path to spectra executable (nil = use PATH)
  executable = nil,

  -- Default arguments passed to all commands
  default_args = {},

  -- Auto-detect epic key from file content
  auto_detect_epic = true,

  -- Show notifications
  notify = true,

  -- Floating window settings
  float = {
    border = "rounded",
    width = 0.8,
    height = 0.8,
  },

  -- Keymaps (set individual keys to false to disable)
  keymaps = {
    validate = "<leader>jv",
    sync = "<leader>js",
    sync_execute = "<leader>jS",
    dashboard = "<leader>jd",
    stories = "<leader>jf",
    init = "<leader>ji",
  },
})
```

## 🎹 Keymaps

| Keymap | Description |
|--------|-------------|
| `<leader>jv` | Validate markdown |
| `<leader>js` | Sync (dry-run) |
| `<leader>jS` | Sync (execute) |
| `<leader>jd` | Show dashboard |
| `<leader>jf` | Find stories (Telescope) |
| `<leader>ji` | Init wizard |

## 📋 Commands

| Command | Description |
|---------|-------------|
| `:SpectraValidate` | Validate markdown file |
| `:SpectraValidate!` | Validate with strict mode |
| `:SpectraSync [epic]` | Sync to Jira (dry-run) |
| `:SpectraSyncExecute [epic]` | Sync to Jira (execute) |
| `:SpectraDashboard` | Show status dashboard |
| `:SpectraInit` | Run setup wizard |
| `:SpectraStories` | Browse stories |

## 🔭 Telescope

Browse content with fuzzy finding:

```vim
:Telescope spectra stories    " Find stories
:Telescope spectra epics      " Find epics
:Telescope spectra commands   " All commands
```

### Telescope Keymaps

| Key | Description |
|-----|-------------|
| `<CR>` | Jump to story/epic |
| `<C-y>` | Copy story ID to clipboard |
| `<C-s>` | Sync selected story |

## 🔌 Lua API

```lua
local spectra = require("spectra")

-- Parse stories from current buffer
local stories = spectra.parse_stories()
-- Returns: { { id = "US-001", title = "...", line = 10 }, ... }

-- Jump to a story
spectra.goto_story("US-001")

-- Detect epic key from buffer
local epic = spectra.detect_epic()

-- Run commands
spectra.validate()
spectra.sync()
spectra.sync_execute()
spectra.dashboard()

-- Run async with callback
spectra.run_async({ "--validate", "--markdown", "epic.md" }, {
  on_complete = function(result)
    print("Exit code:", result.code)
    print("Output:", result.stdout)
  end,
})
```

## 📄 License

MIT License - see [LICENSE](../LICENSE)


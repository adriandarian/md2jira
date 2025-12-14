# Fish completion script for spectra
#
# Installation:
#   Option 1: Copy to Fish completions directory
#     cp spectra.fish ~/.config/fish/completions/spectra.fish
#
#   Option 2: Symlink to Fish completions directory
#     ln -s /path/to/spectra/completions/spectra.fish ~/.config/fish/completions/
#
#   Option 3: Generate dynamically (add to config.fish)
#     spectra --completions fish | source

# Disable file completions by default (we'll enable them for specific options)
complete -c spectra -f

# Required arguments
complete -c spectra -s m -l markdown -d 'Path to markdown epic file' -r -F -a '*.md'
complete -c spectra -s e -l epic -d 'Jira epic key (e.g., PROJ-123)' -x

# Execution mode
complete -c spectra -s x -l execute -d 'Execute changes (default is dry-run)'
complete -c spectra -l no-confirm -d 'Skip confirmation prompts'

# Phase control
complete -c spectra -l phase -d 'Which phase to run' -x -a '
    all\t"Run all sync phases"
    descriptions\t"Sync story descriptions only"
    subtasks\t"Sync subtasks only"
    comments\t"Sync comments only"
    statuses\t"Sync statuses only"
'

# Filters
complete -c spectra -l story -d 'Filter to specific story ID (e.g., US-001)' -x

# Configuration
complete -c spectra -s c -l config -d 'Path to config file' -r -F -a '*.yaml *.yml *.toml'
complete -c spectra -l jira-url -d 'Override Jira URL' -x
complete -c spectra -l project -d 'Override Jira project key' -x

# Output options
complete -c spectra -s v -l verbose -d 'Verbose output'
complete -c spectra -s q -l quiet -d 'Quiet mode - only show errors and summary'
complete -c spectra -s o -l output -d 'Output format' -x -a 'text json'
complete -c spectra -l no-color -d 'Disable colored output'
complete -c spectra -l export -d 'Export analysis to JSON file' -r -F -a '*.json'

# Special modes
complete -c spectra -l validate -d 'Validate markdown file format'
complete -c spectra -s i -l interactive -d 'Interactive mode with step-by-step guided sync'
complete -c spectra -l resume -d 'Resume an interrupted sync session'
complete -c spectra -l resume-session -d 'Resume a specific sync session by ID' -x
complete -c spectra -l list-sessions -d 'List all resumable sync sessions'
complete -c spectra -l version -d 'Show version and exit'
complete -c spectra -s h -l help -d 'Show help message'

# Shell completions
complete -c spectra -l completions -d 'Generate shell completion script' -x -a '
    bash\t"Generate Bash completion script"
    zsh\t"Generate Zsh completion script"  
    fish\t"Generate Fish completion script"
'


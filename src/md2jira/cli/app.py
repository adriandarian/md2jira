"""
CLI App - Main entry point for md2jira command line tool.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from .output import Console, Symbols
from ..adapters import (
    JiraAdapter,
    MarkdownParser,
    ADFFormatter,
    EnvironmentConfigProvider,
)
from ..application import SyncOrchestrator
from ..core.domain.events import EventBus


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="md2jira",
        description="Sync markdown epic documentation with Jira",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze without making changes (dry-run)
  md2jira --markdown EPIC.md --epic PROJ-123

  # Execute sync with confirmations
  md2jira --markdown EPIC.md --epic PROJ-123 --execute

  # Full sync without prompts
  md2jira --markdown EPIC.md --epic PROJ-123 --execute --no-confirm

  # Sync only descriptions
  md2jira --markdown EPIC.md --epic PROJ-123 --execute --phase descriptions

  # Verbose output for debugging
  md2jira --markdown EPIC.md --epic PROJ-123 -v

Environment Variables:
  JIRA_URL         Jira instance URL (e.g., https://company.atlassian.net)
  JIRA_EMAIL       Jira account email
  JIRA_API_TOKEN   Jira API token
        """
    )
    
    # Required arguments
    parser.add_argument(
        "--markdown", "-m",
        type=str,
        required=True,
        help="Path to markdown epic file"
    )
    parser.add_argument(
        "--epic", "-e",
        type=str,
        required=True,
        help="Jira epic key (e.g., PROJ-123)"
    )
    
    # Execution mode
    parser.add_argument(
        "--execute", "-x",
        action="store_true",
        help="Execute changes (default is dry-run)"
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompts"
    )
    
    # Phase control
    parser.add_argument(
        "--phase",
        type=str,
        choices=["all", "descriptions", "subtasks", "comments", "statuses"],
        default="all",
        help="Which phase to run (default: all)"
    )
    
    # Filters
    parser.add_argument(
        "--story",
        type=str,
        help="Filter to specific story ID (e.g., US-001)"
    )
    
    # Configuration
    parser.add_argument(
        "--jira-url",
        type=str,
        help="Override Jira URL"
    )
    parser.add_argument(
        "--project",
        type=str,
        help="Override Jira project key"
    )
    
    # Output options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Export analysis to JSON file"
    )
    
    # Special modes
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate markdown file format"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 2.0.0"
    )
    
    return parser


def validate_markdown(
    console: Console,
    markdown_path: str
) -> bool:
    """Validate markdown file format."""
    console.header("Validating Markdown File")
    
    parser = MarkdownParser()
    errors = parser.validate(markdown_path)
    
    if errors:
        console.error(f"Found {len(errors)} validation error(s):")
        for error in errors:
            console.item(error, "fail")
        return False
    
    console.success("Markdown file is valid!")
    
    # Parse and show summary
    stories = parser.parse_stories(markdown_path)
    console.info(f"Found {len(stories)} user stories")
    
    total_subtasks = sum(len(s.subtasks) for s in stories)
    total_commits = sum(len(s.commits) for s in stories)
    
    console.detail(f"Total subtasks: {total_subtasks}")
    console.detail(f"Total commits: {total_commits}")
    
    return True


def run_sync(
    console: Console,
    args: argparse.Namespace,
) -> int:
    """Run the sync operation."""
    # Load configuration
    config_provider = EnvironmentConfigProvider(cli_overrides=vars(args))
    errors = config_provider.validate()
    
    if errors:
        console.error("Configuration errors:")
        for error in errors:
            console.item(error, "fail")
        return 1
    
    config = config_provider.load()
    
    # Validate markdown exists
    markdown_path = Path(args.markdown)
    if not markdown_path.exists():
        console.error(f"Markdown file not found: {markdown_path}")
        return 1
    
    # Show header
    console.header(f"md2jira {Symbols.ROCKET}")
    
    if config.sync.dry_run:
        console.dry_run_banner()
    
    console.info(f"Markdown: {markdown_path}")
    console.info(f"Epic: {args.epic}")
    console.info(f"Mode: {'Execute' if args.execute else 'Dry-run'}")
    
    # Initialize components
    event_bus = EventBus()
    formatter = ADFFormatter()
    parser = MarkdownParser()
    
    tracker = JiraAdapter(
        config=config.tracker,
        dry_run=config.sync.dry_run,
        formatter=formatter,
    )
    
    # Test connection
    console.section("Connecting to Jira")
    if not tracker.test_connection():
        console.error("Failed to connect to Jira. Check credentials.")
        return 1
    
    user = tracker.get_current_user()
    console.success(f"Connected as: {user.get('displayName', user.get('emailAddress', 'Unknown'))}")
    
    # Configure sync phases
    config.sync.sync_descriptions = args.phase in ("all", "descriptions")
    config.sync.sync_subtasks = args.phase in ("all", "subtasks")
    config.sync.sync_comments = args.phase in ("all", "comments")
    config.sync.sync_statuses = args.phase in ("all", "statuses")
    
    if args.story:
        config.sync.story_filter = args.story
    
    # Create orchestrator
    orchestrator = SyncOrchestrator(
        tracker=tracker,
        parser=parser,
        formatter=formatter,
        config=config.sync,
        event_bus=event_bus,
    )
    
    # Confirmation
    if args.execute and not args.no_confirm:
        if not console.confirm("Proceed with sync execution?"):
            console.warning("Cancelled by user")
            return 0
    
    # Run sync with progress callback
    def progress_callback(phase: str, current: int, total: int) -> None:
        console.progress(current, total, phase)
    
    console.section("Running Sync")
    result = orchestrator.sync(
        markdown_path=str(markdown_path),
        epic_key=args.epic,
        progress_callback=progress_callback,
    )
    
    # Show results
    console.sync_result(result)
    
    # Export if requested
    if args.export:
        import json
        export_data = {
            "success": result.success,
            "dry_run": result.dry_run,
            "matched_stories": result.matched_stories,
            "unmatched_stories": result.unmatched_stories,
            "stats": {
                "stories_matched": result.stories_matched,
                "stories_updated": result.stories_updated,
                "subtasks_created": result.subtasks_created,
                "subtasks_updated": result.subtasks_updated,
                "comments_added": result.comments_added,
                "statuses_updated": result.statuses_updated,
            },
            "errors": result.errors,
            "warnings": result.warnings,
        }
        
        with open(args.export, "w") as f:
            json.dump(export_data, f, indent=2)
        
        console.success(f"Exported results to {args.export}")
    
    return 0 if result.success else 1


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Suppress noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Create console
    console = Console(
        color=not args.no_color,
        verbose=args.verbose,
    )
    
    try:
        # Validate mode
        if args.validate:
            success = validate_markdown(console, args.markdown)
            return 0 if success else 1
        
        # Run sync
        return run_sync(console, args)
        
    except KeyboardInterrupt:
        console.print()
        console.warning("Interrupted by user")
        return 130
    
    except Exception as e:
        console.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def run() -> None:
    """Entry point for console script."""
    sys.exit(main())


if __name__ == "__main__":
    run()


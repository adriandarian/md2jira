"""Spectra Sublime Text plugin commands."""

import subprocess
import os
import re

import sublime
import sublime_plugin


def get_settings():
    """Get Spectra settings."""
    return sublime.load_settings("Spectra.sublime-settings")


def get_spectra_path():
    """Get path to spectra CLI."""
    return get_settings().get("spectra_cli_path", "spectra")


def run_spectra_command(window, args, panel_name="Spectra"):
    """Run a spectra command and show output in panel."""
    view = window.active_view()
    if not view:
        return

    file_path = view.file_name()
    if not file_path:
        sublime.error_message("Please save the file first")
        return

    # Find working directory (project root or file directory)
    working_dir = os.path.dirname(file_path)
    for marker in ["spectra.yaml", "spectra.toml", ".spectra"]:
        parent = file_path
        while parent != os.path.dirname(parent):
            parent = os.path.dirname(parent)
            if os.path.exists(os.path.join(parent, marker)):
                working_dir = parent
                break

    # Build command
    cmd = [get_spectra_path()] + args

    # Create output panel
    panel = window.create_output_panel(panel_name)
    panel.settings().set("line_numbers", False)
    panel.settings().set("gutter", False)
    panel.settings().set("scroll_past_end", False)
    window.run_command("show_panel", {"panel": f"output.{panel_name}"})

    try:
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=60
        )

        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr

        panel.run_command("append", {"characters": output})

        if result.returncode != 0:
            sublime.status_message("Spectra command failed")
        else:
            sublime.status_message("Spectra command completed")

    except subprocess.TimeoutExpired:
        panel.run_command("append", {"characters": "Command timed out"})
        sublime.error_message("Spectra command timed out")
    except FileNotFoundError:
        sublime.error_message(f"Spectra CLI not found. Please install: pip install spectra")
    except Exception as e:
        sublime.error_message(f"Error running Spectra: {str(e)}")


class SpectraValidateCommand(sublime_plugin.WindowCommand):
    """Validate the current Spectra markdown file."""

    def run(self):
        view = self.window.active_view()
        if view:
            view.run_command("save")
            file_path = view.file_name()
            if file_path:
                run_spectra_command(
                    self.window,
                    ["--validate", "--markdown", file_path],
                    "Spectra Validate"
                )


class SpectraSyncCommand(sublime_plugin.WindowCommand):
    """Sync the current file to the issue tracker."""

    def run(self):
        view = self.window.active_view()
        if view:
            view.run_command("save")
            file_path = view.file_name()
            if file_path:
                if sublime.ok_cancel_dialog("Sync this file to the tracker?"):
                    run_spectra_command(
                        self.window,
                        ["--sync", "--markdown", file_path],
                        "Spectra Sync"
                    )


class SpectraPlanCommand(sublime_plugin.WindowCommand):
    """Preview changes before syncing."""

    def run(self):
        view = self.window.active_view()
        if view:
            view.run_command("save")
            file_path = view.file_name()
            if file_path:
                run_spectra_command(
                    self.window,
                    ["plan", "--markdown", file_path],
                    "Spectra Plan"
                )


class SpectraDiffCommand(sublime_plugin.WindowCommand):
    """Show diff between local file and tracker state."""

    def run(self):
        view = self.window.active_view()
        if view:
            view.run_command("save")
            file_path = view.file_name()
            if file_path:
                run_spectra_command(
                    self.window,
                    ["diff", "--markdown", file_path],
                    "Spectra Diff"
                )


class SpectraImportCommand(sublime_plugin.WindowCommand):
    """Import stories from tracker."""

    def run(self):
        self.window.show_input_panel(
            "Output file:",
            "stories.md",
            self.on_done,
            None,
            None
        )

    def on_done(self, output_file):
        run_spectra_command(
            self.window,
            ["import", "--output", output_file],
            "Spectra Import"
        )


class SpectraExportCommand(sublime_plugin.WindowCommand):
    """Export the current file."""

    def run(self):
        self.window.show_quick_panel(
            ["HTML", "PDF", "JSON", "CSV", "DOCX"],
            self.on_select
        )

    def on_select(self, index):
        if index < 0:
            return

        formats = ["html", "pdf", "json", "csv", "docx"]
        fmt = formats[index]

        view = self.window.active_view()
        if view:
            view.run_command("save")
            file_path = view.file_name()
            if file_path:
                base_name = os.path.splitext(file_path)[0]
                output_file = f"{base_name}.{fmt}"
                run_spectra_command(
                    self.window,
                    ["export", "--markdown", file_path, "--format", fmt, "--output", output_file],
                    "Spectra Export"
                )


class SpectraStatsCommand(sublime_plugin.WindowCommand):
    """Show statistics for the current file."""

    def run(self):
        view = self.window.active_view()
        if view:
            view.run_command("save")
            file_path = view.file_name()
            if file_path:
                run_spectra_command(
                    self.window,
                    ["stats", "--markdown", file_path],
                    "Spectra Stats"
                )


class SpectraDoctorCommand(sublime_plugin.WindowCommand):
    """Run diagnostics on the Spectra setup."""

    def run(self):
        run_spectra_command(self.window, ["doctor"], "Spectra Doctor")


class SpectraOpenInTrackerCommand(sublime_plugin.TextCommand):
    """Open the story at cursor in the tracker."""

    def run(self, edit):
        # Get current line
        sel = self.view.sel()[0]
        line = self.view.line(sel)
        line_text = self.view.substr(line)

        # Look for tracker ID
        match = re.search(r'\[([A-Z][A-Z0-9]*-[0-9]+)\]', line_text)
        if match:
            issue_id = match.group(1)
            run_spectra_command(
                self.view.window(),
                ["open", issue_id],
                "Spectra Open"
            )
            return

        # Look for GitHub-style ID
        match = re.search(r'#(\d+)', line_text)
        if match:
            issue_num = match.group(0)
            run_spectra_command(
                self.view.window(),
                ["open", issue_num],
                "Spectra Open"
            )
            return

        sublime.status_message("No issue ID found at cursor")


class SpectraNewStoryCommand(sublime_plugin.TextCommand):
    """Insert a new story template."""

    def run(self, edit):
        self.view.window().show_input_panel(
            "Story title:",
            "",
            lambda title: self.insert_story(edit, title),
            None,
            None
        )

    def insert_story(self, edit, title):
        template = f"""
## Story: {title}
**Status**: Todo
**Priority**: Medium
**Points**:

### Description

TODO: Add description

### Acceptance Criteria
- [ ]

"""
        self.view.run_command("insert", {"characters": template})


class SpectraNewEpicCommand(sublime_plugin.TextCommand):
    """Insert a new epic template."""

    def run(self, edit):
        self.view.window().show_input_panel(
            "Epic title:",
            "",
            lambda title: self.insert_epic(edit, title),
            None,
            None
        )

    def insert_epic(self, edit, title):
        template = f"""
# Epic: {title}

TODO: Add epic description

"""
        self.view.run_command("insert", {"characters": template})


class SpectraNewSubtaskCommand(sublime_plugin.TextCommand):
    """Insert a new subtask template."""

    def run(self, edit):
        self.view.window().show_input_panel(
            "Subtask title:",
            "",
            lambda title: self.insert_subtask(edit, title),
            None,
            None
        )

    def insert_subtask(self, edit, title):
        template = f"""
## Subtask: {title}
**Status**: Todo

"""
        self.view.run_command("insert", {"characters": template})


class SpectraEventListener(sublime_plugin.EventListener):
    """Event listener for Spectra files."""

    def on_post_save_async(self, view):
        """Validate on save if enabled."""
        settings = get_settings()
        if not settings.get("validate_on_save", True):
            return

        file_path = view.file_name()
        if not file_path:
            return

        # Check if this is a Spectra file
        if not (file_path.endswith(".spectra.md") or
                file_path.endswith("user-stories.md") or
                file_path.endswith("backlog.md") or
                self._is_spectra_file(view)):
            return

        # Run validation silently
        view.window().run_command("spectra_validate")

    def _is_spectra_file(self, view):
        """Check if the view contains Spectra headers."""
        content = view.substr(sublime.Region(0, min(2000, view.size())))
        return bool(re.search(r'^##?\s*(Epic|Story|Subtask):', content, re.MULTILINE))

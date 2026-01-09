"""File watcher for monitoring Claude Code log files using watchdog."""

import asyncio
from pathlib import Path
from typing import Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent


class ClaudeLogHandler(FileSystemEventHandler):
    """Handle file system events for Claude Code logs."""

    def __init__(self, callback: Callable[[Path], None]):
        """Initialize file event handler.

        Args:
            callback: Function to call when file changes detected
        """
        super().__init__()
        self.callback = callback

    def on_modified(self, event: FileSystemEvent):
        """Called when a file is modified.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        if file_path.suffix == ".jsonl" and "agent-" in file_path.name:
            self.callback(file_path)

    def on_created(self, event: FileSystemEvent):
        """Called when a file is created.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        if file_path.suffix == ".jsonl" and "agent-" in file_path.name:
            self.callback(file_path)


class LogFileWatcher:
    """Watch Claude Code log files for changes using watchdog."""

    def __init__(self, claude_home: Path, callback: Callable[[Path], None]):
        """Initialize file watcher.

        Args:
            claude_home: Path to Claude home directory
            callback: Function to call when files change
        """
        self.claude_home = claude_home
        self.callback = callback
        self.observer: Optional[Observer] = None
        self.handler: Optional[ClaudeLogHandler] = None

    def start(self):
        """Start watching for file changes."""
        projects_dir = self.claude_home / "projects"

        if not projects_dir.exists():
            projects_dir.mkdir(parents=True, exist_ok=True)

        self.handler = ClaudeLogHandler(self.callback)
        self.observer = Observer()
        self.observer.schedule(self.handler, str(projects_dir), recursive=True)
        self.observer.start()

    def stop(self):
        """Stop watching for file changes."""
        if self.observer:
            self.observer.stop()
            self.observer.join()

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        self.stop()

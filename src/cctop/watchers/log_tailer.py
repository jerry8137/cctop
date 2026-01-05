from pathlib import Path
from typing import List, Dict


class LogTailer:
    """Efficiently read only new lines from log files (tail-like behavior)"""

    def __init__(self):
        self.file_positions: Dict[str, tuple[int, int]] = {}

    def get_new_lines(self, file_path: Path) -> List[str]:
        """Get only new lines since last read"""
        if not file_path.exists():
            return []

        file_key = str(file_path)

        try:
            stat = file_path.stat()
            current_size = stat.st_size
            current_inode = stat.st_ino

            last_position = 0
            last_inode = None

            if file_key in self.file_positions:
                last_position, last_inode = self.file_positions[file_key]

            if last_inode is not None and last_inode != current_inode:
                last_position = 0

            if current_size < last_position:
                last_position = 0

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(last_position)
                new_lines = f.readlines()
                new_position = f.tell()

            self.file_positions[file_key] = (new_position, current_inode)

            return new_lines

        except (IOError, OSError):
            return []

    def reset(self, file_path: Path = None):
        """Reset position tracking for a file or all files"""
        if file_path:
            file_key = str(file_path)
            if file_key in self.file_positions:
                del self.file_positions[file_key]
        else:
            self.file_positions.clear()

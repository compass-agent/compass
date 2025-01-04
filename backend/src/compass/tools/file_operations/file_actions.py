from dataclasses import dataclass
from typing import Any, Literal, Optional, get_args
from collections import defaultdict
import os
from pathlib import Path

from ...tools.base import BaseAnthropicTool, ToolResult, ToolError
from ...constants import HOST_WORKING_DIR

Command = Literal[
    "view",
    "create",
    "str_replace",
    "insert",
    "undo_edit",
]

@dataclass
class FileState:
    """Tracks the state of a file for undo operations"""
    content: str
    exists: bool

class FileOperationsTool(BaseAnthropicTool):
    api_type: Literal["text_editor_20241022"] = "text_editor_20241022"
    name: Literal["str_replace_editor"] = "str_replace_editor"

    def __init__(self):
        self._file_history = defaultdict(list)
        self.base_path = Path(HOST_WORKING_DIR)

    async def __call__(
        self,
        *,
        command: Command,
        path: str,
        file_text: str | None = None,
        view_range: list[int] | None = None,
        old_str: str | None = None,
        new_str: str | None = None,
        insert_line: int | None = None,
        **kwargs,
    ) -> ToolResult:
        """Execute the requested file operation"""
        _path = Path(path)
        self.validate_path(command, _path)
        
        if command == "view":
            return await self._view(_path, view_range)
        elif command == "create":
            if file_text is None:
                raise ToolError("Parameter `file_text` is required for command: create")
            return await self._create(_path, file_text)
        elif command == "str_replace":
            if old_str is None:
                raise ToolError("Parameter `old_str` is required for command: str_replace")
            return await self._str_replace(_path, old_str, new_str)
        elif command == "insert":
            if insert_line is None:
                raise ToolError("Parameter `insert_line` is required for command: insert")
            if new_str is None:
                raise ToolError("Parameter `new_str` is required for command: insert")
            return await self._insert(_path, insert_line, new_str)
        elif command == "undo_edit":
            return await self._undo_edit(_path)
            
        raise ToolError(
            f'Unrecognized command {command}. The allowed commands for the {self.name} tool are: {", ".join(get_args(Command))}'
        )

    def validate_path(self, command: str, path: Path):
        """Check that the path/command combination is valid."""
        # Convert relative paths to be relative to our working directory
        if not path.is_absolute():
            path = self.base_path / path
            
        if not path.exists() and command != "create":
            raise ToolError(f"The path {path} does not exist. Please provide a valid path.")
        if path.exists() and command == "create":
            raise ToolError(f"File already exists at: {path}. Cannot overwrite files using command `create`.")
        if path.is_dir() and command != "view":
            raise ToolError(f"The path {path} is a directory and only the `view` command can be used on directories")

    # Update method signatures to match the new __call__ parameters
    async def _view(self, path: Path, view_range: list[int] | None = None) -> ToolResult:
        """View contents of a file"""
        try:
            # Convert relative paths to absolute
            if not path.is_absolute():
                path = self.base_path / path
                
            if not path.exists():
                return ToolResult(error=f"File not found: {path}")
            
            with open(path, 'r') as f:
                content = f.read()
            return ToolResult(output=content)
        except Exception as e:
            return ToolResult(error=str(e))

    async def _create(self, path: Path, content: str) -> ToolResult:
        """Create a new file with content"""
        try:
            # Convert relative paths to absolute
            if not path.is_absolute():
                path = self.base_path / path
                
            os.makedirs(path.parent, exist_ok=True)
            with open(path, 'w') as f:
                f.write(content)
            
            self._file_history[path].append(content)
            return ToolResult(output=f"Created file: {path}")
        except Exception as e:
            return ToolResult(error=str(e))

    async def _str_replace(self, path: Path, old_str: str, new_str: str | None) -> ToolResult:
        """Replace text in a file"""
        try:
            with open(path, 'r') as f:
                content = f.read()
            
            new_str = new_str if new_str is not None else ""
            new_content = content.replace(old_str, new_str)
            
            self._file_history[path].append(content)
            
            with open(path, 'w') as f:
                f.write(new_content)
                
            return ToolResult(output=f"Replaced text in {path}")
        except Exception as e:
            return ToolResult(error=str(e))

    async def _insert(self, path: Path, line_number: int, content: str) -> ToolResult:
        """Insert text at specific line number"""
        try:
            with open(path, 'r') as f:
                lines = f.readlines()
            
            self._file_history[path].append(''.join(lines))
            
            if line_number < 1 or line_number > len(lines) + 1:
                return ToolResult(error=f"Invalid line number: {line_number}")
            
            lines.insert(line_number - 1, content + '\n')
            
            with open(path, 'w') as f:
                f.writelines(lines)
                
            return ToolResult(output=f"Inserted text at line {line_number} in {path}")
        except Exception as e:
            return ToolResult(error=str(e))

    async def _undo_edit(self, path: Path) -> ToolResult:
        """Undo last edit operation"""
        try:
            if not self._file_history[path]:
                return ToolResult(error=f"No edit history found for: {path}")
            
            previous_content = self._file_history[path].pop()
            with open(path, 'w') as f:
                f.write(previous_content)
                
            return ToolResult(output=f"Undid last change to {path}")
        except Exception as e:
            return ToolResult(error=str(e))

    def to_params(self):
        """Return tool parameters as defined by Anthropic"""
        return {
            "type": self.api_type,
            "name": self.name,
        } 
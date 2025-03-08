from dataclasses import dataclass
from typing import Literal, get_args
from collections import defaultdict
import os
from pathlib import Path

from compass.tools.base import BaseTool
from compass.types.agent import ToolResult, ToolError
from compass.constants import HOST_WORKING_DIR

Command = Literal[
    "view",
    "create",
    "str_replace",
    "insert",
    "undo_edit",
]

MAX_PREFIX_CHARS = 10000
MAX_SUFFIX_CHARS = 1000

@dataclass
class FileState:
    """Tracks the state of a file for undo operations"""
    content: str
    exists: bool

class FileOperationsTool(BaseTool):
    api_type: Literal["text_editor_20250124"] = "text_editor_20250124"
    name: Literal["str_replace_editor"] = "str_replace_editor"

    def __init__(self):
        self._file_history = defaultdict(list)
        self.base_path = Path(HOST_WORKING_DIR)
        # Create base directory if it doesn't exist
        os.makedirs(self.base_path, exist_ok=True)

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
            
        raise ToolError(f'Unrecognized command {command}. The allowed commands for the {self.name} tool are: {", ".join(get_args(Command))}')

    def validate_path(self, command: str, path: Path):
        """Check that the path/command combination is valid."""
        # Convert relative paths to be relative to our working directory
        if not path.is_absolute():
            path = self.base_path / path
            
        # Special handling for create command
        if command == "create":
            if path.exists():
                raise ToolError(f"File already exists at: {path}. Cannot overwrite files using command `create`.")
            # Ensure parent directory exists
            os.makedirs(path.parent, exist_ok=True)
            return

        if not path.exists():
            raise ToolError(f"The path {path} does not exist. Please provide a valid path.")
        if path.is_dir() and command != "view":
            raise ToolError(f"The path {path} is a directory and only the `view` command can be used on directories")

        try:
            path.relative_to(self.base_path)
        except ValueError:
            raise ToolError(f"Access denied: {path} is outside the working directory")

    # Update method signatures to match the new __call__ parameters
    async def _view(self, path: Path, view_range: list[int] | None = None) -> ToolResult:
        """View contents of a file or directory structure"""
        try:
            if not path.is_absolute():
                path = self.base_path / path
                
            if not path.exists():
                raise ToolError(f"Path not found: {path}")

            if path.is_dir():
                # Show directory structure using tree-like format
                tree_content = []
                for root, dirs, files in os.walk(path):
                    level = root[len(str(path)):].count(os.sep)
                    indent = "│   " * level
                    tree_content.append(f"{indent}📁 {os.path.basename(root)}/")
                    subindent = "│   " * (level + 1)
                    for f in files:
                        tree_content.append(f"{subindent}📄 {f}")
                
                return ToolResult(text="\n".join(tree_content))
            else:
                # Handle file content as before
                with open(path, 'r') as f:
                    content = f.read()
                    
                if len(content) > MAX_PREFIX_CHARS + MAX_SUFFIX_CHARS:
                    prefix = content[:MAX_PREFIX_CHARS]
                    suffix = content[-MAX_SUFFIX_CHARS:]
                    skipped_chars = len(content) - (MAX_PREFIX_CHARS + MAX_SUFFIX_CHARS)
                    content = f"[Showing first {MAX_PREFIX_CHARS} and last {MAX_SUFFIX_CHARS} characters. Skipping {skipped_chars} characters in the middle...]\n\n{prefix}\n\n[...]\n\n{suffix}"
                    
                return ToolResult(text=content)
        except Exception as e:
            raise ToolError(str(e))

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
            return ToolResult(text=f"Created file: {path}")
        except Exception as e:
            raise ToolError(str(e))

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
                
            return ToolResult(text=f"Replaced text in {path}")
        except Exception as e:
            raise ToolError(str(e))

    async def _insert(self, path: Path, line_number: int, content: str) -> ToolResult:
        """Insert text at specific line number"""
        try:
            with open(path, 'r') as f:
                lines = f.readlines()
            
            self._file_history[path].append(''.join(lines))
            
            if line_number < 1 or line_number > len(lines) + 1:
                raise ToolError(f"Invalid line number: {line_number}")
            
            lines.insert(line_number - 1, content + '\n')
            
            with open(path, 'w') as f:
                f.writelines(lines)
                
            return ToolResult(text=f"Inserted text at line {line_number} in {path}")
        except Exception as e:
            raise ToolError(str(e))

    async def _undo_edit(self, path: Path) -> ToolResult:
        """Undo last edit operation"""
        try:
            if not self._file_history[path]:
                raise ToolError(f"No edit history found for: {path}")
            
            previous_content = self._file_history[path].pop()
            with open(path, 'w') as f:
                f.write(previous_content)
                
            return ToolResult(text=f"Undid last change to {path}")
        except Exception as e:
            raise ToolError(str(e))

    def to_params(self):
        """Return tool parameters as defined by Anthropic"""
        return {
            "type": self.api_type,
            "name": self.name,
            "description": """A text editor tool that can view, create, edit, and undo changes to files.
Supports operations like viewing file contents, creating new files, replacing text, and inserting lines.""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "enum": ["view", "create", "str_replace", "insert", "undo_edit"],
                        "description": "The operation to perform on the file"
                    },
                    "path": {
                        "type": "string",
                        "description": "Path to the file to operate on"
                    },
                    "file_text": {
                        "type": "string",
                        "description": "Content to write when creating a new file"
                    },
                    "view_range": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Optional line range to view [start, end]"
                    },
                    "old_str": {
                        "type": "string",
                        "description": "Text to replace when using str_replace command"
                    },
                    "new_str": {
                        "type": "string",
                        "description": "Replacement text for str_replace command or new content for insert command"
                    },
                    "insert_line": {
                        "type": "integer",
                        "description": "Line number where to insert new content"
                    }
                },
                "required": ["command", "path"]
            }
        } 
from dataclasses import dataclass
from typing import Any, Literal, Optional
from collections import defaultdict
import os

from ...tools.base import BaseAnthropicTool, ToolResult, ToolError

@dataclass
class FileState:
    """Tracks the state of a file for undo operations"""
    content: str
    exists: bool

class FileOperationsTool(BaseAnthropicTool):
    """Tool for file operations including view, create, edit and undo capabilities"""

    api_type: Literal["text_editor_20241022"] = "text_editor_20241022"
    name: Literal["str_replace_editor"] = "str_replace_editor"

    def __init__(self):
        self._file_history = defaultdict(list)

    def _save_state(self, path: str, content: str, exists: bool):
        """Save file state for undo operations"""
        self._file_history[path].append(FileState(content, exists))

    def _get_previous_state(self, path: str) -> Optional[FileState]:
        """Get the previous file state for undo operations"""
        history = self._file_history[path]
        if len(history) > 1:
            history.pop()  # Remove current state
            return history[-1]
        return None

    async def __call__(self, *, command: str, path: str, **kwargs) -> ToolResult:
        """Execute the requested file operation"""
        operations = {
            "view": self._view,
            "create": self._create,
            "str_replace": self._str_replace,
            "insert": self._insert,
            "undo_edit": self._undo_edit
        }
        
        if command not in operations:
            raise ToolError(f"Unknown command: {command}")
            
        return await operations[command](path=path, **kwargs)

    async def _view(self, *, path: str, **kwargs) -> ToolResult:
        """View contents of a file"""
        try:
            if not os.path.exists(path):
                return ToolResult(error=f"File not found: {path}")
            
            with open(path, 'r') as f:
                content = f.read()
            return ToolResult(output=content)
        except Exception as e:
            return ToolResult(error=str(e))

    async def _create(self, *, path: str, content: str, **kwargs) -> ToolResult:
        """Create a new file with content"""
        try:
            if os.path.exists(path):
                return ToolResult(error=f"File already exists: {path}")
            
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write(content)
            
            self._save_state(path, content, True)
            return ToolResult(output=f"Created file: {path}")
        except Exception as e:
            return ToolResult(error=str(e))

    async def _str_replace(self, *, path: str, old_text: str, new_text: str, **kwargs) -> ToolResult:
        """Replace text in a file"""
        try:
            if not os.path.exists(path):
                return ToolResult(error=f"File not found: {path}")
            
            with open(path, 'r') as f:
                content = f.read()
            
            self._save_state(path, content, True)
            
            new_content = content.replace(old_text, new_text)
            with open(path, 'w') as f:
                f.write(new_content)
                
            return ToolResult(output=f"Replaced text in {path}")
        except Exception as e:
            return ToolResult(error=str(e))

    async def _insert(self, *, path: str, line_number: int, content: str, **kwargs) -> ToolResult:
        """Insert text at specific line number"""
        try:
            if not os.path.exists(path):
                return ToolResult(error=f"File not found: {path}")
            
            with open(path, 'r') as f:
                lines = f.readlines()
            
            self._save_state(path, ''.join(lines), True)
            
            if line_number < 1 or line_number > len(lines) + 1:
                return ToolResult(error=f"Invalid line number: {line_number}")
            
            lines.insert(line_number - 1, content + '\n')
            
            with open(path, 'w') as f:
                f.writelines(lines)
                
            return ToolResult(output=f"Inserted text at line {line_number} in {path}")
        except Exception as e:
            return ToolResult(error=str(e))

    async def _undo_edit(self, *, path: str, **kwargs) -> ToolResult:
        """Undo last edit operation"""
        try:
            previous_state = self._get_previous_state(path)
            if not previous_state:
                return ToolResult(error=f"No previous state found for: {path}")
            
            if previous_state.exists:
                with open(path, 'w') as f:
                    f.write(previous_state.content)
            else:
                os.remove(path)
                
            return ToolResult(output=f"Undid last change to {path}")
        except Exception as e:
            return ToolResult(error=str(e))

    def to_params(self):
        """Return tool parameters as defined by Anthropic"""
        return {
            "type": self.api_type,
            "name": self.name,
        } 
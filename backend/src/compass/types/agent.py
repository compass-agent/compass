from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import StrEnum

@dataclass
class SystemMessage:
    content: str
    
    def to_dict(self) -> dict:
        return {
            "content": self.content
        }

@dataclass
class HumanMessage:
    content: str
    image_data: Optional[str] = None  # base64 encoded image
    
    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "image_data": self.image_data
        }

class ToolError(Exception):
    """Base exception class for all tool-related errors."""
    pass

@dataclass
class ToolResult:
    tool_call_id: Optional[str] = None
    text: Optional[str] = None
    system: Optional[str] = None
    image: Optional[str] = None
    error: Optional[str] = None

    def with_tool_id(self, tool_id: str) -> None:
        """Updates the tool_call_id in place."""
        self.tool_call_id = tool_id    
    def to_dict(self) -> dict:
        return {
            "tool_call_id": self.tool_call_id,
            "text": self.text,
            "system": self.system,
            "image": self.image,
            "error": self.error
        }

@dataclass
class ToolCall:
    name: str
    args: Dict[str, Any]
    tool_call_id: str
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "args": self.args,
            "tool_call_id": self.tool_call_id
        }

@dataclass
class AIMessage:
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    
    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "tool_calls": [tc.to_dict() for tc in (self.tool_calls or [])]
        }

class ScalingSource(StrEnum):
    COMPUTER = "computer"
    API = "api"

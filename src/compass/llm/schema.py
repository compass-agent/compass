from dataclasses import dataclass
from typing import Optional, Dict, Any, List

@dataclass
class SystemMessage:
    content: str

@dataclass
class HumanMessage:
    content: str
    image_data: Optional[str] = None  # base64 encoded image

@dataclass
class ToolResult:
    text: Optional[str] = None
    image: Optional[str] = None
    error: Optional[str] = None

@dataclass
class ToolCall:
    name: str
    args: Dict[str, Any]
    tool_call_id: str

@dataclass
class AIMessage:
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None 
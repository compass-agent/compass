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



### FROM OLD CODE
# @dataclass(kw_only=True, frozen=True)
# class ToolResult:
#     """Represents the result of a tool execution."""

#     output: str | None = None
#     error: str | None = None
#     base64_image: str | None = None
#     system: str | None = None

#     def __bool__(self):
#         return any(getattr(self, field.name) for field in fields(self))

#     def __add__(self, other: "ToolResult"):
#         def combine_fields(
#             field: str | None, other_field: str | None, concatenate: bool = True
#         ):
#             if field and other_field:
#                 if concatenate:
#                     return field + other_field
#                 raise ValueError("Cannot combine tool results")
#             return field or other_field

#         return ToolResult(
#             output=combine_fields(self.output, other.output),
#             error=combine_fields(self.error, other.error),
#             base64_image=combine_fields(self.base64_image, other.base64_image, False),
#             system=combine_fields(self.system, other.system),
#         )

#     def replace(self, **kwargs):
#         """Returns a new ToolResult with the given fields replaced."""
#         return replace(self, **kwargs)


"""Collection classes for managing multiple tools."""

from typing import Any, Dict, List

from anthropic.types.beta import BetaToolUnionParam
from compass.types.agent import ToolResult, ToolCall
from .base import BaseTool # tbr

class ToolCollection:
    """A collection of anthropic-defined tools."""

    def __init__(self, *tools: BaseTool):
        self.tools = tools
        self.tool_map = {tool.to_params()["name"]: tool for tool in tools}

    def to_params(
        self,
    ) -> List[Dict[str, Any]]:
        return [tool.to_params() for tool in self.tools]

    async def run(self, tool_call: ToolCall) -> ToolResult:
        tool = self.tool_map.get(tool_call.name)
        if not tool:
            ToolResult(tool_call_id=tool_call.tool_call_id, error=f"Tool {tool_call.name} is invalid")
        try:
            if tool is None:
                return ToolResult(tool_call_id=tool_call.tool_call_id, error=f"Tool {tool_call.name} is invalid")
            result = await tool(**tool_call.args)
            result.with_tool_id(tool_call.tool_call_id)
            return result
        except Exception as e:
            return ToolResult(tool_call_id=tool_call.tool_call_id, error=str(e))

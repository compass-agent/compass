"""Collection classes for managing multiple tools."""

from typing import Any, Dict, List, Optional

from compass.types.agent import ToolResult, ToolCall, ToolError
from .base import BaseTool

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
        """Execute a tool and ensure all errors are captured in ToolResult."""
        try:
            tool = self.tool_map.get(tool_call.name)
            if not tool:
                return ToolResult(
                    tool_call_id=tool_call.tool_call_id, 
                    error=f"Tool {tool_call.name} is invalid"
                )
            result = await tool(**tool_call.args)
            result.with_tool_id(tool_call.tool_call_id)
            return result
            
        except ToolError as te:
            error_message = str(te)
            return ToolResult(
                tool_call_id=tool_call.tool_call_id,
                error=error_message
            )
        except Exception as e:
            # Handle all other unexpected errors
            error_message = f"Unexpected error during tool execution: {str(e)}"
            return ToolResult(
                tool_call_id=tool_call.tool_call_id,
                error=error_message
            )
    
    async def connect_tool(self, tool_name: str) -> ToolResult:
        """Connect to a specific tool if it supports connection."""
        tool = self.tool_map.get(tool_name)
        if not tool:
            return ToolResult(error=f"Tool {tool_name} is invalid")
        
        # Use type checking to avoid linter errors
        try:
            # Check for tool-specific connection methods
            connect_method = None
            if tool_name == 'sap_com':
                connect_method = getattr(tool, 'connect_to_sap', None)
            elif tool_name == 'computer':
                connect_method = getattr(tool, 'connect_to_desktop', None)
            
            if connect_method and callable(connect_method):
                return await connect_method()  # type: ignore
            else:
                return ToolResult(error=f"Tool {tool_name} does not support connection")
        except AttributeError:
            return ToolResult(error=f"Tool {tool_name} does not support connection")
    
    def get_tool_connection_status(self, tool_name: str) -> Optional[str]:
        """Get the connection status of a specific tool if it supports it."""
        tool = self.tool_map.get(tool_name)
        if not tool:
            return None
        
        # Use type checking to avoid linter errors
        try:
            # Check if the tool has get_connection_status method dynamically
            status_method = getattr(tool, 'get_connection_status', None)
            if status_method and callable(status_method):
                return status_method()  # type: ignore
            else:
                return None
        except AttributeError:
            return None

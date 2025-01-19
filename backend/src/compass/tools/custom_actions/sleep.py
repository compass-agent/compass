import asyncio
import logging
from typing import Literal, TypedDict

from anthropic.types.beta import BetaToolUnionParam
from compass.types.agent import ToolResult, ToolError
from compass.tools.base import BaseTool
logger = logging.getLogger(__name__)

class SleepParams(TypedDict):
    action: Literal["sleep"]
    time: float

class SleepAction(BaseTool):
    """A tool that allows the agent to pause execution for a specified duration."""

    name: Literal["custom_action"] = "custom_action"

    def to_params(self) -> BetaToolUnionParam:
        return {
            "name": self.name,
            "description": "Allows pausing execution for a specified duration in seconds",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["sleep"],
                        "description": "The action to perform (sleep)"
                    },
                    "time": {
                        "type": "number",
                        "description": "Time to sleep in seconds"
                    }
                },
                "required": ["action", "time"]
            }
        } # type: ignore

    async def __call__(self, *, action: Literal["sleep"], time: float) -> ToolResult:
        if action != "sleep":
            logger.error(f"Invalid action '{action}' for custom_action tool")
            raise ToolError(f"Invalid action '{action}' for custom_action tool")
        try:
            logger.info(f"Sleeping for {time} seconds")
            await asyncio.sleep(time)
            return ToolResult(text=f"Successfully slept for {time} seconds")
        except Exception as e:
            error_msg = f"Error during sleep: {str(e)}"
            logger.error(error_msg)
            raise ToolError(error_msg) 
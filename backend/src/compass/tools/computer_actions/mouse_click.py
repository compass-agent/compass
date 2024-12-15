import pyautogui
import logging
from typing import Optional, Tuple, Literal

from ..base import ToolResult, ToolError
from .base import BaseComputerAction

logger = logging.getLogger(__name__)

class MouseClickAction(BaseComputerAction):
    """Handles mouse click actions."""

    async def execute(self, 
                action: Literal["left_click", "right_click", "middle_click", "double_click"],
                coordinate: Optional[Tuple[int, int]] = None) -> ToolResult:
        """Handle mouse click actions at the current cursor position."""

        try:
            logger.info(f"Executing click action: {action}")
            if coordinate is not None:
                raise ToolError(f"coordinate is not accepted for {action}")
            
            # Execute click actions synchronously since they're quick operations
            if action == "double_click":
                pyautogui.doubleClick()
            else:
                button = {
                    "left_click": "left",
                    "right_click": "right",
                    "middle_click": "middle"
                }[action]
                pyautogui.click(button=button)
                
            logger.info(f"Click action completed: {action}")

            # Take screenshot
            base64_image = await self.capture_and_process_screenshot()
            logger.info(f"Screenshot captured and processed: for {action} to be added to its response")
            return ToolResult(
                output=None, 
                error=None, 
                base64_image=base64_image
            ) 
        except Exception as e:
            logger.error(f"Error in MouseClickAction.execute: {e}", exc_info=True)
            raise ToolError(f"Error executing MouseClickAction: {e}")
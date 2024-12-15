import pyautogui
import logging
from typing import Optional, Tuple, Literal

from ..base import ToolResult, ToolError
from .base import BaseComputerAction

logger = logging.getLogger(__name__)

class MouseClickAction(BaseComputerAction):
    """Handles mouse click actions."""

    def execute(self, 
                action: Literal["left_click", "right_click", "middle_click", "double_click"],
                coordinate: Optional[Tuple[int, int]] = None) -> ToolResult:
        """Handle mouse click actions at the current cursor position."""

        logger.info(f"Executing click action: {action}")
        if coordinate is not None:
            raise ToolError(f"coordinate is not accepted for {action}")
        
        if action == "double_click":
            pyautogui.doubleClick()
        else:
            button = {
                "left_click": "left",
                "right_click": "right",
                "middle_click": "middle"
            }[action]
            pyautogui.click(button=button)
            
        logger.info(f"Executing click action: {action}")
        return ToolResult(output=None, error=None, base64_image=self.capture_and_process_screenshot()) 
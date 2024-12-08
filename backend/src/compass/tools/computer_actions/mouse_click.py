import pyautogui
import logging
from typing import Optional, Tuple, Literal

from ..base import ToolResult, ToolError
from .base import BaseComputerAction

logger = logging.getLogger(__name__)

class MouseClickAction(BaseComputerAction):
    """Handles mouse click actions."""

    def execute(self, 
                action: Literal["left_click", "right_click"],
                coordinate: Optional[Tuple[int, int]] = None) -> ToolResult:
        """Handle mouse click actions at the current cursor position."""
        if coordinate is not None:
            raise ToolError(f"coordinate is not accepted for {action}")
        
        button = 'left' if action == "left_click" else 'right'
        pyautogui.click(button=button)
        logger.info(f"Executing click action: {action}")
        
        return ToolResult(output=None, error=None) 
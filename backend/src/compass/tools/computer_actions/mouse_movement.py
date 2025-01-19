import pyautogui
import logging
from typing import Optional, Tuple, Literal

from compass.types.agent import ToolResult, ScalingSource
from .base import BaseComputerAction

logger = logging.getLogger(__name__)

class MouseMovementAction(BaseComputerAction):
    """Handles mouse movement and drag actions."""

    async def execute(self, 
                action: Literal["mouse_move", "left_click_drag"] = "mouse_move",
                coordinate: Optional[Tuple[int, int]] = None) -> ToolResult:
        """Handle mouse movement or drag to specified coordinates."""
        
        if coordinate is None:
            logger.error(f"coordinate is required for {action} action")
            raise ToolError(f"coordinate is required for {action} action")
            
        if not all(isinstance(i, int) and i >= 0 for i in coordinate):
            logger.error(f"{coordinate} must be a tuple of non-negative ints for {action} action")
            raise ToolError(f"{coordinate} must be a tuple of non-negative ints for {action} action")
        
        x, y = self.scale_coordinates(ScalingSource.API, coordinate[0], coordinate[1])
        logger.info(f"Executing {action} action, with coordinate {coordinate[0]}, {coordinate[1]} scaled to {x},{y}")

        if action == "left_click_drag":
            pyautogui.mouseDown(button='left')
            pyautogui.moveTo(x, y, duration=0)
            pyautogui.mouseUp(button='left')
        else:
            pyautogui.moveTo(x, y, duration=0)

        return ToolResult(output=None, error=None)
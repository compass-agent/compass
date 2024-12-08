import pyautogui
import logging
from typing import Optional, Tuple

from ..base import ToolResult, ToolError, ScalingSource
from .base import BaseComputerAction

logger = logging.getLogger(__name__)

class MouseMovementAction(BaseComputerAction):
    """Handles mouse movement actions."""

    def execute(self, coordinate: Optional[Tuple[int, int]] = None) -> ToolResult:
        """Handle mouse movement to specified coordinates."""
        logger.info("Executing mouse_move action")
        
        if coordinate is None:
            logger.error("coordinate is required for mouse_move")
            raise ToolError("coordinate is required for mouse_move")
            
        if not all(isinstance(i, int) and i >= 0 for i in coordinate):
            logger.error(f"{coordinate} must be a tuple of non-negative ints")
            raise ToolError(f"{coordinate} must be a tuple of non-negative ints")
        
        x, y = self.scale_coordinates(ScalingSource.API, coordinate[0], coordinate[1])
        logger.info(f"scaling back AI suggested mouse move to {x},{y} from {coordinate[0]},{coordinate[1]}")
        pyautogui.moveTo(x, y)
        
        return ToolResult(output=None, error=None) 
import pyautogui
import logging
from typing import Optional, Tuple

from ..base import ToolResult, ToolError, ScalingSource
from .base import BaseComputerAction

logger = logging.getLogger(__name__)

class CursorPositionAction(BaseComputerAction):
    """Handles getting cursor position with proper scaling."""

    def execute(self, coordinate: Optional[Tuple[int, int]] = None, text: Optional[str] = None) -> ToolResult:
        """Get the current cursor position."""
        logger.info("Executing cursor_position")
        
        if coordinate is not None:
            logger.error("coordinate is not accepted for cursor_position")
            raise ToolError("coordinate is not accepted for cursor_position")
        if text is not None:
            raise ToolError("text is not accepted for cursor_position")

        x, y = pyautogui.position()
        scaled_x, scaled_y = self.scale_coordinates(ScalingSource.COMPUTER, round(x), round(y))
        logger.info(f"scaled cursor position to {scaled_x},{scaled_y} from {x},{y}")
        
        return ToolResult(output=f"X={scaled_x},Y={scaled_y}", error=None) 
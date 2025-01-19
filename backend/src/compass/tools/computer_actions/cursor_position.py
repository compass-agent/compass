import logging
from typing import Optional, Tuple

from compass.types.agent import ToolResult
from .base import BaseComputerAction

logger = logging.getLogger(__name__)

class CursorPositionAction(BaseComputerAction):
    """Handles getting cursor position with proper scaling."""
    
    async def execute(self, coordinate: Optional[Tuple[int, int]] = None, text: Optional[str] = None) -> ToolResult:
        """Get the current cursor position."""
        logger.info("Executing cursor_position")
        
        if coordinate is not None:
            logger.error("coordinate is not accepted for cursor_position")
            return ToolResult(error="coordinate is not accepted for cursor_position")
        if text is not None:
            logger.error("text is not accepted for cursor_position")
            return ToolResult(error="text is not accepted for cursor_position")

        scaled_x, scaled_y = await self.get_cursor_position()
        return ToolResult(text=f"X={scaled_x},Y={scaled_y}") 

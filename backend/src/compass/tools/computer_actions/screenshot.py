import logging

from ..base import ToolResult, ToolError
from .base import BaseComputerAction

logger = logging.getLogger(__name__)

class ScreenshotAction(BaseComputerAction):
    """Handles taking and processing screenshots."""

    def execute(self, **kwargs) -> ToolResult:
        """Take and process a screenshot with proper scaling and optimization in memory"""
        try:
            base64_image = self.capture_and_process_screenshot()
            cursor_position_x, cursor_position_y = self.get_cursor_position()

            return ToolResult(
                output=f"The cursor position when the screenshot was taken was X={cursor_position_x},Y={cursor_position_y}",
                error=None,
                base64_image=base64_image
            )
        except Exception as e:
            logger.error(f"Screenshot failed: {str(e)}")
            raise ToolError(f"Failed to take screenshot: {str(e)}") 
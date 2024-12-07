import logging
from typing import Optional

from ..base import ToolResult, ToolError
from .base import BaseComputerAction

logger = logging.getLogger(__name__)

class ScreenshotAction(BaseComputerAction):
    """Handles taking and processing screenshots."""

    def execute(self, **kwargs) -> ToolResult:
        """Take and process a screenshot with proper scaling and optimization in memory"""
        try:
            base64_image = self.capture_and_process_screenshot()
            return ToolResult(
                output=None,
                error=None,
                base64_image=base64_image
            )
        except Exception as e:
            logger.error(f"Screenshot failed: {str(e)}")
            raise ToolError(f"Failed to take screenshot: {str(e)}") 
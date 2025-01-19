import logging

from compass.types.agent import ToolResult, ToolError
from .base import BaseComputerAction
from compass.services.state_manager import StateManager

logger = logging.getLogger(__name__)

class ScreenshotAction(BaseComputerAction):
    """Handles taking and processing screenshots."""

    def __init__(self, width: int, height: int, scaled_width: int, scaled_height: int, state_manager: StateManager):
        super().__init__(
            width=width,
            height=height,
            scaled_width=scaled_width,
            scaled_height=scaled_height,
            state_manager=state_manager,
            enable_screenshot_comparison=True,
            enable_screen_description=False
        )

    async def execute(self, **kwargs) -> ToolResult:
        """Take and process a screenshot with proper scaling and optimization in memory"""
        try:
            screenshot_result = await self.capture_and_process_screenshot()
            cursor_position_x, cursor_position_y = await self.get_cursor_position()

            output_parts = [
                f"The cursor position when the screenshot was taken was X={cursor_position_x},Y={cursor_position_y}"
            ]

            if screenshot_result.description:
                output_parts.append("\nScreen Description:")
                output_parts.append(screenshot_result.description)

            return ToolResult(
                text="\n".join(output_parts),
                image=screenshot_result.base64_image
            )
        except Exception as e:
            logger.error(f"Screenshot failed: {str(e)}")
            raise ToolError(f"Failed to take screenshot: {str(e)}")

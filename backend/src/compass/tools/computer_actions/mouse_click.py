import pyautogui
import logging
from typing import Optional, Tuple, Literal
import time
from compass.types.agent import ToolResult
from .base import BaseComputerAction
from compass.services.state_manager import StateManager
from compass.constants import ENABLE_SCREEN_DESCRIPTION_MOUSE_CLICK, ENABLE_SCREENSHOT_COMPARISON_MOUSE_CLICK, TIME_TO_WAIT_AFTER_CLICK_BEFORE_SCREENSHOT

logger = logging.getLogger(__name__)

class MouseClickAction(BaseComputerAction):
    """Handles mouse click actions."""

    def __init__(self, width: int, height: int, scaled_width: int, scaled_height: int, state_manager: StateManager):
        super().__init__(
            width=width,
            height=height,
            scaled_width=scaled_width,
            scaled_height=scaled_height,
            state_manager=state_manager,
            enable_screenshot_comparison=ENABLE_SCREENSHOT_COMPARISON_MOUSE_CLICK,
            enable_screen_description=ENABLE_SCREEN_DESCRIPTION_MOUSE_CLICK
        )

    async def execute(self, 
                action: Literal["left_click", "right_click", "middle_click", "double_click"],
                coordinate: Optional[Tuple[int, int]] = None) -> ToolResult:
        """Handle mouse click actions at the current cursor position."""

        try:
            logger.info(f"Executing click action: {action}")
            if coordinate is not None:
                logger.error(f"coordinate is not accepted for {action}")
                return ToolResult(error=f"coordinate is not accepted for {action}")
            
            # Execute click actions
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

            # wait slightly before taking screenshot
            time.sleep(TIME_TO_WAIT_AFTER_CLICK_BEFORE_SCREENSHOT)
            screenshot_result = await self.capture_and_process_screenshot()
            
            output_parts = []
            
            if screenshot_result.has_changed is False:
                output_parts.append(f"Important: The screen did not change after executing this {action} action. Was that the desired outcome? If NOT, please run this action again, before continuing.")
            
            if screenshot_result.description:
                output_parts.append("\nScreen Description:")
                output_parts.append(screenshot_result.description)
            
            return ToolResult(
                text="\n".join(output_parts), 
                image=screenshot_result.base64_image
            ) 
        except Exception as e:
            logger.error(f"Error in MouseClickAction.execute: {e}", exc_info=True)
            return ToolResult(error=f"Error executing MouseClickAction: {e}")

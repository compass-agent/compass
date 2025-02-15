import pyautogui
import logging
import time
from typing import Optional, Literal

from compass.types.agent import ToolResult
from .base import BaseComputerAction

logger = logging.getLogger(__name__)

TYPING_DELAY_MS = 10
TYPING_GROUP_SIZE = 50

class KeyboardInputAction(BaseComputerAction):
    """Handles keyboard input actions."""

    async def execute(self,
                action: Literal["key", "type"],
                text: Optional[str] = None) -> ToolResult:
        """Handle keyboard input actions."""
        if text is None:
            logger.error(f"text is required for {action}")
            return ToolResult(error=f"text is required for {action}")

        if action == "key":
            logger.info(f"Executing key action: {text}")
            pyautogui.press(text)
            return ToolResult(text=None)
        else:  # type action
            logger.info(f"Executing type action: {text}")
            chunks = [text[i:i + TYPING_GROUP_SIZE] 
                     for i in range(0, len(text), TYPING_GROUP_SIZE)]
            
            for chunk in chunks:
                pyautogui.write(chunk, TYPING_DELAY_MS/1000)
                if len(chunks) > 1:
                    time.sleep(TYPING_DELAY_MS / 1000)
            return ToolResult(
                image=(await self.capture_and_process_screenshot()).base64_image
            ) 

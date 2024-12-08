import pyautogui
from PIL import Image
import io
import base64
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
            # Step 1: Capture screenshot directly to memory
            screenshot = pyautogui.screenshot()
            
            # Step 2: Scale image
            scaled_screenshot = screenshot.resize(
                (self.scaled_width, self.scaled_height),
                resample=Image.Resampling.LANCZOS
            )
            
            # Step 3: Reduce color depth (replacing pngquant)
            optimized_screenshot = scaled_screenshot.quantize(
                colors=256,  # 8-bit color depth
                method=Image.FASTOCTREE  # type: ignore # Fast and efficient method
            )
            
            # Step 4: Save to memory buffer and encode
            buffer = io.BytesIO()
            optimized_screenshot.save(
                buffer,
                format='PNG',
                optimize=True  # Additional PNG optimization
            )
            
            # Step 5: Convert to base64
            base64_image = base64.b64encode(buffer.getvalue()).decode()
            
            return ToolResult(
                output=None,
                error=None,
                base64_image=base64_image
            )

        except Exception as e:
            logger.error(f"Screenshot failed: {str(e)}")
            raise ToolError(f"Failed to take screenshot: {str(e)}") 
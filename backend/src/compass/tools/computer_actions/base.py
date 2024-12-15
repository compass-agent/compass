import pyautogui
from PIL import Image
import io
import base64
from abc import ABC, abstractmethod
from typing import Tuple
import logging
import asyncio

from ..base import ToolResult, ScalingSource, ToolError
from compass.utils.utility import log_execution_time


logger = logging.getLogger(__name__)

class BaseComputerAction(ABC):
    """Base class for all computer actions."""
    
    def __init__(self, width: int, height: int, scaled_width: int, scaled_height: int):
        self.width = width
        self.height = height
        self.scaled_width = scaled_width
        self.scaled_height = scaled_height
        self._x_scaling_factor = scaled_width / width
        self._y_scaling_factor = scaled_height / height

    # @log_execution_time(logger)
    async def capture_and_process_screenshot(self) -> str:
        """Core method to capture and process screenshot, returning base64 string"""
        try:
            logger.info("Capturing and processing screenshot")
            # Take screenshot synchronously
            screenshot = pyautogui.screenshot()
            
            logger.info(f"Scaling screenshot from {self.width}x{self.height} to {self.scaled_width}x{self.scaled_height}")
            # Do image processing synchronously
            scaled_screenshot = screenshot.resize(
                (self.scaled_width, self.scaled_height),
                resample=Image.Resampling.LANCZOS
            )
            
            # Reduce color depth synchronously
            logger.info(f"Reducing color depth from 256 to 8-bit")
            optimized_screenshot = scaled_screenshot.quantize(
                colors=256,  # 8-bit color depth
                method=Image.FASTOCTREE  # Fast and efficient method
            )
            
            # Save to memory buffer synchronously
            logger.info(f"Saving to memory buffer and encoding to base64")
            buffer = io.BytesIO()
            optimized_screenshot.save(
                buffer,
                format='PNG',
                optimize=True  # Additional PNG optimization
            )
            
            # Convert to base64
            logger.info(f"Converting to base64")
            return base64.b64encode(buffer.getvalue()).decode()
        except Exception as e:
            logger.error(f"Error in capture_and_process_screenshot: {e}", exc_info=True)
            return ""

    async def get_cursor_position(self) -> Tuple[int, int]:
        """Get the current cursor position and scale it."""
        x, y = await asyncio.to_thread(pyautogui.position)
        scaled_x, scaled_y = self.scale_coordinates(ScalingSource.COMPUTER, round(x), round(y))
        logger.info(f"scaled cursor position to {scaled_x},{scaled_y} from {x},{y}")
        return scaled_x, scaled_y

    def scale_coordinates(self, source: ScalingSource, x: int, y: int) -> tuple[int, int]:
        """Scale coordinates using pre-calculated scaling factors."""
        if source == ScalingSource.API:
            if x > self.scaled_width or y > self.scaled_height:
                message = f"Coordinates {x}, {y} are out of bounds ({self.scaled_width}, {self.scaled_height})"
                logger.error(message)
                raise ToolError(message)
            return round(x / self._x_scaling_factor), round(y / self._y_scaling_factor)
        else:
            return round(x * self._x_scaling_factor), round(y * self._y_scaling_factor)

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the computer action."""
        pass 
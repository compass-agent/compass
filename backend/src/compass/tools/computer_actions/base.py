import pyautogui
from PIL import Image # type: ignore
import io
import base64
from abc import ABC, abstractmethod
from typing import Tuple
import logging
import asyncio
from dataclasses import dataclass

from ..base import ToolResult, ScalingSource, ToolError
from compass.services.state_manager import StateManager
from compass.constants import SCREENSHOT_OPTIMIZATION
from compass.tools.screen_parser.screen_parser import ScreenParser
from compass.tools.screen_parser.models import ScreenData

logger = logging.getLogger(__name__)

@dataclass
class ScreenshotResult:
    """Data class to hold screenshot capture results."""
    base64_image: str
    has_changed: bool | None = None  # None when comparison wasn't requested
    error: str | None = None  # To capture any errors that occurred
    description: str | None = None  # Screen parser description

class BaseComputerAction(ABC):
    """Base class for all computer actions."""
    
    def __init__(self, 
                 width: int, 
                 height: int, 
                 scaled_width: int, 
                 scaled_height: int, 
                 state_manager: StateManager,
                 enable_screenshot_comparison: bool = False,
                 enable_screen_description: bool = False):
        self.width = width
        self.height = height
        self.scaled_width = scaled_width
        self.scaled_height = scaled_height
        self._x_scaling_factor = scaled_width / width
        self._y_scaling_factor = scaled_height / height
        self.state_manager = state_manager
        self._last_screenshot = None if not enable_screenshot_comparison else None
        self.screen_parser = ScreenParser() if enable_screen_description else None
        self._enable_screenshot_comparison = enable_screenshot_comparison
        self._enable_screen_description = enable_screen_description
        
    # @log_execution_time(logger)
    async def capture_and_process_screenshot(self) -> ScreenshotResult:
        """Core method to capture and process screenshot, returning a ScreenshotResult object"""
        try:
            logger.info("Capturing and processing screenshot")
            screenshot = pyautogui.screenshot()
            
            logger.info(f"Scaling screenshot from {self.width}x{self.height} to {self.scaled_width}x{self.scaled_height}")
            scaled_screenshot = screenshot.resize(
                (self.scaled_width, self.scaled_height),
                resample=Image.Resampling.LANCZOS
            )
            
            logger.info(f"Reducing color depth from 256 to 8-bit")
            optimized_screenshot = scaled_screenshot.quantize(
                colors=256,
                method=Image.FASTOCTREE  # type: ignore
            )
            
            has_changed = None
            if self._enable_screenshot_comparison and self._last_screenshot is not None:
                has_changed = optimized_screenshot.tobytes() != self._last_screenshot.tobytes()
                logger.info(f"Screenshot comparison result: changed={has_changed}")
            
            if self._enable_screenshot_comparison:
                self._last_screenshot = optimized_screenshot
            
            logger.info(f"Saving to memory buffer and encoding to base64")
            buffer = io.BytesIO()
            optimized_screenshot.save(
                buffer,
                format='PNG',
                optimize=True
            )
            base64_result = base64.b64encode(buffer.getvalue()).decode()
            
            description = None
            if self._enable_screen_description and self.screen_parser:
                # Create ScreenData object and get description using light parse
                logger.info("Running light screen parsing")
                screen_data = ScreenData(
                    image_data=base64_result,
                    elements=[],
                    description=None
                )
                parsed_data = self.screen_parser.light_parse(screen_data)
                description = parsed_data.description
            
            return ScreenshotResult(
                base64_image=base64_result,
                has_changed=has_changed,
                description=description
            )

        except Exception as e:
            error_msg = f"Error in capture_and_process_screenshot: {e}"
            logger.error(error_msg, exc_info=True)
            return ScreenshotResult(
                base64_image="",
                has_changed=None,
                error=error_msg,
                description=None
            )

    async def get_cursor_position(self) -> Tuple[int, int]:
        """Get the current cursor position and scale it."""
        x, y = pyautogui.position()
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
import pyautogui
from PIL import Image
import io
import base64
from abc import ABC, abstractmethod
from typing import Tuple
import logging
from dataclasses import dataclass
from time import time
import cv2
import numpy as np
import json

from compass.types.agent import ToolResult, ScalingSource
from compass.services.state_manager import StateManager
from compass.tools.screen_parser.screen_parser import ScreenParser
from compass.tools.screen_parser.models import ScreenData
from compass.utils.utility import log_execution_time
from compass.utils.utility import SessionManager

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

    @log_execution_time(logger)
    async def capture_and_process_screenshot(self) -> ScreenshotResult:
        """Core method to capture and process screenshot, returning a ScreenshotResult object
        """
        try:
            logger.info("Capturing screenshot")
            screenshot = self._take_screenshot(use_logical_dimensions=True)
            
            # Save original screenshot
            self._save_original_screenshot(screenshot)
            
            description = None
            screen_data = None
            if self._enable_screen_description and self.screen_parser:
                # Run screen parsing on original screenshot before scaling
                logger.info("Running light screen parsing on original image")
                screen_data = ScreenData(
                    image_data=self._image_to_base64(screenshot),
                    elements=[],
                    description=None
                )
                # Pass scaling factors to light_parse
                parsed_data = self.screen_parser.light_parse(
                    screen_data,
                    x_scaling_factor=self._x_scaling_factor,
                    y_scaling_factor=self._y_scaling_factor
                )
                description = parsed_data.description
                # Save processed screenshot with bounding boxes
                if parsed_data.elements:
                    self._save_processed_screenshot(screenshot, parsed_data)

            has_changed = None
            if self._enable_screenshot_comparison and self._last_screenshot is not None:
                has_changed = screenshot.tobytes() != self._last_screenshot.tobytes()
                logger.info(f"Screenshot comparison result: changed={has_changed}")
            
            if self._enable_screenshot_comparison:
                self._last_screenshot = screenshot
            
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
            
            base64_result = self._image_to_base64(optimized_screenshot)
            
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

    @log_execution_time(logger)
    def _take_screenshot(self, use_logical_dimensions: bool = True) -> Image.Image:
        """Helper method to capture screenshot with either logical or physical dimensions.
        """
        screenshot = pyautogui.screenshot()
        if use_logical_dimensions:
            logical_width, logical_height = pyautogui.size()
            screenshot = screenshot.resize(
                (logical_width, logical_height),
                resample=Image.Resampling.LANCZOS
            )
            logger.info(f"Screenshot resized to logical dimensions: {screenshot.width}x{screenshot.height}")
        return screenshot

    def _save_original_screenshot(self, screenshot: Image.Image) -> None:
        """Helper method to save the original screenshot to the session directory."""
        try:
            history_tracker = SessionManager.get_history_tracker()
            if history_tracker:
                timestamp = history_tracker.get_timestamp_filename()
                screenshot_path = history_tracker.screenshots_dir / f"screenshot_{timestamp}.png"
                screenshot.save(screenshot_path, format='PNG')
                logger.info(f"Saved original screenshot with timestamp {timestamp}")
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")

    def _save_processed_screenshot(self, screenshot: Image.Image, screen_data: ScreenData) -> None:
        """Helper method to save the processed screenshot with bounding boxes to the session directory."""
        try:
            history_tracker = SessionManager.get_history_tracker()
            if history_tracker and screen_data.elements:
                # Convert PIL Image to cv2 format
                cv2_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                
                # Prepare data for JSON
                bounding_boxes = []

                # Draw rectangles for each detected element
                for element in screen_data.elements:
                    coords = element.coordinates
                    x1, y1 = int(coords['x1']), int(coords['y1'])
                    x2, y2 = int(coords['x2']), int(coords['y2'])
                    
                    # Draw green rectangle
                    cv2.rectangle(cv2_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Add caption/text above the box
                    label = element.text or element.caption or "unnamed"
                    cv2.putText(cv2_image, label, (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    # Append bounding box data
                    bounding_boxes.append({
                        "label": label,
                        "coordinates": {
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2
                        }
                    })

                # Save the annotated image
                timestamp = history_tracker.get_timestamp_filename()
                screenshot_path = history_tracker.screenshots_dir / f"screenshot_{timestamp}_annotated.png"
                cv2.imwrite(str(screenshot_path), cv2_image)
                logger.info(f"Saved annotated screenshot with timestamp {timestamp}")

                # Save bounding box data as JSON
                json_path = history_tracker.screenshots_dir / f"screenshot_{timestamp}_bounding_boxes.json"
                with open(json_path, 'w') as json_file:
                    json.dump(bounding_boxes, json_file, indent=4)
                logger.info(f"Saved bounding box data as JSON with timestamp {timestamp}")

        except Exception as e:
            logger.error(f"Failed to save annotated screenshot or bounding box data: {e}")

    def _image_to_base64(self, image: Image.Image) -> str:
        """Helper method to convert PIL Image to base64 string"""
        buffer = io.BytesIO()
        image.save(
            buffer,
            format='PNG',
            optimize=True
        )
        return base64.b64encode(buffer.getvalue()).decode()

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
                raise ValueError(message)
            return round(x / self._x_scaling_factor), round(y / self._y_scaling_factor)
        else:
            return round(x * self._x_scaling_factor), round(y * self._y_scaling_factor)

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the computer action."""
        pass 
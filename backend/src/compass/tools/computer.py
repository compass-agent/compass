import pyautogui
import base64
from PIL import Image
import shlex
from pathlib import Path
from typing import Literal, TypedDict, Optional
from uuid import uuid4
import logging
import time
from datetime import datetime
from enum import StrEnum
import subprocess

from anthropic.types.beta import BetaToolComputerUse20241022Param

from .base import BaseAnthropicTool, ToolError, ToolResult
from .run import run
from compass.constants import SCREENSHOT_SCALE_FACTOR, SCREENSHOT_COLOR_DEPTH, KEEP_SCREENSHOTS, SCALING_ENABLED
from compass.utils.utility import HistoryLogger

OUTPUT_DIR = "/tmp/outputs"

logger = logging.getLogger(__name__)

Action = Literal[
    "screenshot",
    "left_click",
    "right_click",
    "key",
    "type",
    "mouse_move",
    "cursor_position",
]

TYPING_DELAY_MS = 12
TYPING_GROUP_SIZE = 50

class Resolution(TypedDict):
    width: int
    height: int

class ScalingSource(StrEnum):
    COMPUTER = "computer"
    API = "api"

MAX_SCALING_TARGETS: dict[str, Resolution] = {
    "XGA": Resolution(width=1024, height=768),    # 4:3 1.33333
    "WXGA": Resolution(width=1280, height=800),   # 16:10 1.6
    "FWXGA": Resolution(width=1366, height=768),  # ~16:9 1.77864
}

class ComputerToolOptions(TypedDict):
    display_height_px: int
    display_width_px: int

class ComputerTool(BaseAnthropicTool):
    """
    A tool that allows the agent to interact with the screen of the current computer (MacOS).
    Currently supports taking screenshots.
    Other actions are placeholders for future implementation.
    """

    name: Literal["computer"] = "computer"
    api_type: Literal["computer_20241022"] = "computer_20241022"
    width: int
    height: int

    _screenshot_delay = 2.0
    _scaling_enabled = SCALING_ENABLED
    _scaling_factor = SCREENSHOT_SCALE_FACTOR

    @property
    def options(self) -> ComputerToolOptions:
        return {
            "display_width_px": self.scaled_width, 
            "display_height_px": self.scaled_height,
        }

    def to_params(self) -> BetaToolComputerUse20241022Param:
        return {"name": self.name, "type": self.api_type, **self.options}

    def __init__(self, history_tracker: 'HistoryLogger'):
        super().__init__()
        logger.info("Initializing ComputerTool")
        self.history_tracker = history_tracker        
        self.width, self.height = pyautogui.size()
        logger.info(f"Original dimensions: {self.width}, {self.height}")
        
        if not (self.width and self.height):
            logger.error("Could not determine screen dimensions, thus quitting") 
            raise ToolError("Could not determine screen dimensions")

        logger.info("Finding best target dimension, XGA, WXGA, FWXGA...")
        self._find_best_standard_dimension()
        
        logger.info(f"Computer works with image dimensions of {self.width}x{self.height}")
        logger.info(f"Agent will be working with image dimensions of {self.scaled_width}x{self.scaled_height}")
 
    def _find_best_standard_dimension(self) -> None:
        """
        Find the best matching standard resolution based on aspect ratio.
        """
        ratio = self.width / self.height
        logger.info(f"checking for best standard dimension that matches aspect ratio of {ratio}")
        
        base_x_scale = base_y_scale = 1.0
        match_found = False
        for dimension in MAX_SCALING_TARGETS.values():
            # Set tolerance to 0.06 to catch appropriate ratios
            if abs(dimension["width"] / dimension["height"] - ratio) < 0.064 and dimension["width"] < self.width:
                logger.info(f"Found best standard dimension ratios: {dimension}")
                # Calculate scaling factors
                base_x_scale = dimension["width"] / self.width
                base_y_scale = dimension["height"] / self.height
                logger.info(f"base scaling factors: {base_x_scale}, {base_y_scale}")
                match_found = True
                break
        
        if not match_found:
            logger.warning(f"No matching standard dimensions found for ratio {ratio:.3f} (dimensions: {self.width}x{self.height})")

        self._x_scaling_factor = base_x_scale * self._scaling_factor
        self._y_scaling_factor = base_y_scale * self._scaling_factor
        logger.info(f"final scaling factors: {self._x_scaling_factor}, {self._y_scaling_factor}")
        self.scaled_width = round(self.width * self._x_scaling_factor)
        self.scaled_height = round(self.height * self._y_scaling_factor)
        logger.info(f"scaled dimensions: {self.scaled_width}, {self.scaled_height}")

    def scale_coordinates(self, source: ScalingSource, x: int, y: int) -> tuple[int, int]:
        """Scale coordinates using pre-calculated scaling factors."""
        if not self._scaling_enabled: # FIXME: Check make sure we used it during init
            return x, y

        if source == ScalingSource.API:
            if x > self.scaled_width or y > self.scaled_height:
                message = f"Coordinates {x}, {y} are out of bounds ({self.scaled_width}, {self.scaled_height})"
                logger.error(message)
                raise ToolError(message)
            return round(x / self._x_scaling_factor), round(y / self._y_scaling_factor)
        else:
            return round(x * self._x_scaling_factor), round(y * self._y_scaling_factor)

    def __call__(
        self,
        *,
        action: Action,
        text: str | None = None,
        coordinate: tuple[int, int] | None = None,
        **kwargs,
    ):
        if action == "screenshot":
            return self.screenshot()
        elif action in ("left_click", "right_click"):
            return self.handle_click(action, coordinate)
        elif action in ("key", "type"):
            return self.handle_text_input(action, text)
        elif action == "mouse_move":
            return self._handle_mouse_action(action, coordinate)
        elif action == "cursor_position":
            return self.get_cursor_position(coordinate, text)
        else:
            raise ToolError(f"Action '{action}' is not implemented yet.")

    def handle_click(
        self, 
        action: Literal["left_click", "right_click"], 
        coordinate: tuple[int, int] | None
    ) -> ToolResult:
        """Handle mouse click actions at the current cursor position."""
        if coordinate is not None:
            raise ToolError(f"coordinate is not accepted for {action}")
        
        button = 'left' if action == "left_click" else 'right'
        pyautogui.click(button=button)
        logger.info(f"Executing click action: {action}")
        return ToolResult(output=None, error=None)

    def handle_text_input(
        self,
        action: Literal["key", "type"],
        text: str | None
    ) -> ToolResult:
        """Handle keyboard input actions."""
        if text is None:
            logger.error(f"text is required for {action}")
            raise ToolError(f"text is required for {action}")

        if action == "key":
            logger.info(f"Executing key action: {text}")
            pyautogui.press(text)
            return ToolResult(output=None, error=None)
        else:  # type action
            logger.info(f"Executing type action: {text}")
            chunks = [text[i:i + TYPING_GROUP_SIZE] 
                     for i in range(0, len(text), TYPING_GROUP_SIZE)]
            
            for chunk in chunks:
                pyautogui.write(chunk, interval=TYPING_DELAY_MS/1000)
                if len(chunks) > 1:
                    time.sleep(TYPING_DELAY_MS / 1000)
            return ToolResult(output=None, error=None)

    def screenshot(self):
        """Take and process a screenshot with proper scaling"""
        start_time = time.time()
        
        try:
            timestamp = datetime.now().strftime('%H_%M_%S')
            original_path = self.history_tracker.screenshots_dir / f"{timestamp}__1.png"
            scaled_path = self.history_tracker.screenshots_dir / f"{timestamp}__2.png"
            final_path = self.history_tracker.screenshots_dir / f"{timestamp}__3.png"
            
            # Step 1: Take screenshot
            start_time = time.time()
            screenshot = pyautogui.screenshot()
            logger.info(f"Screenshot capture took {(time.time() - start_time) * 1000:.2f}ms")
            start_time = time.time()
            screenshot.save(str(original_path))
            logger.info(f"Screenshot saving took {(time.time() - start_time) * 1000:.2f}ms")
            
            if not original_path.exists():
                logger.error("Failed to take screenshot")
                raise ToolError("Failed to take screenshot")
            logger.info(f"took screenshot to {original_path}, dimensions {self.width}x{self.height}, size: {original_path.stat().st_size / 1024:.1f}kb")
            
            # Step 2: Scale image
            start_time = time.time()
            with Image.open(original_path) as img:
                img = img.resize((self.scaled_width, self.scaled_height), Image.Resampling.LANCZOS)
                img.save(scaled_path)
            logger.info(f"Image scaling took {(time.time() - start_time) * 1000:.2f}ms")

            if not scaled_path.exists():
                logger.error("Failed to scale screenshot")
                raise ToolError("Failed to scale screenshot")
            logger.info(f"scaled screenshot to {scaled_path} with dimensions {self.scaled_width}x{self.scaled_height}, size: {scaled_path.stat().st_size / 1024:.1f}kb")

            # Step 3: Optimize image
            start_time = time.time()
            try:
                optimize_cmd = (
                    f"pngquant '{SCREENSHOT_COLOR_DEPTH}' "
                    f"--quality=0-85 --speed 1 --force "
                    f"--output {shlex.quote(str(final_path))} "
                    f"{shlex.quote(str(scaled_path))}"
                )
                subprocess.run(optimize_cmd, shell=True, check=True, capture_output=True)
                
                if not final_path.exists():
                    logger.warning("pngquant optimization failed, using scaled image")
                    final_path = scaled_path
                
            except (subprocess.SubprocessError, FileNotFoundError):
                logger.warning("pngquant not available, using scaled image")
                final_path = scaled_path
            logger.info(f"Image optimization took {(time.time() - start_time) * 1000:.2f}ms")
            
            logger.info(f"optimized screenshot to {final_path}, size: {final_path.stat().st_size / 1024:.1f}kb")

            # Step 4: Read and encode
            processed_bytes = final_path.read_bytes()
            base64_image = base64.b64encode(processed_bytes).decode()
            
            return ToolResult(
                output=None,
                error=None,
                base64_image=base64_image
            )

        finally:
            if not KEEP_SCREENSHOTS:
                for path in (original_path, scaled_path, final_path):
                    if path.exists():
                        path.unlink()

    def _handle_mouse_action(self, action: str, coordinate: tuple[int, int] | None = None) -> ToolResult:
        """Handle mouse-related actions."""
        logger.info(f"Executing mouse action: {action}")
        if action == "mouse_move":
            if coordinate is None:
                logger.error("coordinate is required for mouse_move")
                raise ToolError("coordinate is required for mouse_move")
            if not all(isinstance(i, int) and i >= 0 for i in coordinate):
                logger.error(f"{coordinate} must be a tuple of non-negative ints")
                raise ToolError(f"{coordinate} must be a tuple of non-negative ints")
            
            x, y = self.scale_coordinates(ScalingSource.API, coordinate[0], coordinate[1])
            logger.info(f"scaling back AI suggested mouse move to {x},{y} from {coordinate[0]},{coordinate[1]}")
            pyautogui.moveTo(x, y)
            return ToolResult(output=None, error=None)
        
        raise ToolError(f"Unsupported mouse action: {action}")

    def get_cursor_position(self, coordinate: tuple[int, int] | None = None, text: str | None = None) -> ToolResult:
        """Get the current cursor position."""
        logger.info("Executing cursor_position")
        if coordinate is not None:
            logger.error("coordinate is not accepted for cursor_position")
            raise ToolError("coordinate is not accepted for cursor_position")
        if text is not None:
            raise ToolError("text is not accepted for cursor_position")

        x, y = pyautogui.position()
        scaled_x, scaled_y = self.scale_coordinates(ScalingSource.COMPUTER, round(x), round(y))
        logger.info(f"scaled cursor position to {scaled_x},{scaled_y} from {x},{y}")
        return ToolResult(output=f"X={scaled_x},Y={scaled_y}", error=None)

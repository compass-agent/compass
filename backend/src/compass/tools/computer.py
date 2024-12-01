import subprocess
import base64
import os
import shlex
from pathlib import Path
from typing import Literal, TypedDict, Optional
from uuid import uuid4
import re
import logging
import time
from datetime import datetime
from enum import StrEnum

from anthropic.types.beta import BetaToolComputerUse20241022Param

from .base import BaseAnthropicTool, ToolError, ToolResult
from .run import run
from compass.constants import SCREENSHOT_SCALE_FACTOR, SCREENSHOT_COLOR_DEPTH, KEEP_SCREENSHOTS
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
    "XGA": Resolution(width=1024, height=768),    # 4:3
    "WXGA": Resolution(width=1280, height=800),   # 16:10
    "FWXGA": Resolution(width=1366, height=768),  # ~16:9
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
    _scaling_enabled = True
    _scaling_factor = SCREENSHOT_SCALE_FACTOR

    @property
    def options(self) -> ComputerToolOptions:
        return {
            "display_width_px": self.width,
            "display_height_px": self.height,
        }

    def to_params(self) -> BetaToolComputerUse20241022Param:
        return {"name": self.name, "type": self.api_type, **self.options}

    def __init__(self, history_tracker: 'HistoryLogger'):
        super().__init__()
        
        # Store history tracker instance
        self.history_tracker = history_tracker
        
        # Get original dimensions
        self._original_width, self._original_height = get_screen_dimensions()
        
        # Store the original dimensions
        self.width = self._original_width
        self.height = self._original_height
        
        if not (self.width and self.height):
            raise ToolError("Could not determine screen dimensions")

        # Calculate target dimensions and scaling factors once
        self._target_dimension = self._find_best_target_dimension()
        if self._target_dimension:
            base_x_scale = self._target_dimension["width"] / self.width
            base_y_scale = self._target_dimension["height"] / self.height
            self._x_scaling_factor = base_x_scale * self._scaling_factor
            self._y_scaling_factor = base_y_scale * self._scaling_factor
        else:
            self._x_scaling_factor = self._y_scaling_factor = self._scaling_factor

    def _find_best_target_dimension(self) -> Optional[Resolution]:
        """Find the best matching target resolution based on aspect ratio."""
        ratio = self.width / self.height
        
        for dimension in MAX_SCALING_TARGETS.values():
            # Allow small error in aspect ratio
            if abs(dimension["width"] / dimension["height"] - ratio) < 0.02:
                if dimension["width"] < self.width:
                    logger.info(f"Found best target dimension rations: {dimension}")
                    return dimension
        logger.info("No best target dimension found")
        return None

    def scale_coordinates(self, source: ScalingSource, x: int, y: int) -> tuple[int, int]:
        """Scale coordinates using pre-calculated scaling factors."""
        if not self._scaling_enabled:
            return x, y

        if source == ScalingSource.API:
            # Scale up from API to computer coordinates
            if x > self.width or y > self.height:
                logger.error(f"Coordinates {x}, {y} are out of bounds ({self.width}, {self.height})")
                raise ToolError(f"Coordinates {x}, {y} are out of bounds")
            return round(x / self._x_scaling_factor), round(y / self._y_scaling_factor)
        else:
            # Scale down from computer to API coordinates
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
        """Handle mouse click actions at the current cursor position.
        
        Args:
            action: The type of click action ("left_click" or "right_click")
            
        Returns:
            ToolResult: The result of the click action
        """
        if coordinate is not None:
            raise ToolError(f"coordinate is not accepted for {action}")
        
        click_type = "c" if action == "left_click" else "rc"
        logger.info(f"Executing click action: {click_type}")
        return self.shell(f"cliclick {click_type}")

    def handle_text_input(
        self,
        action: Literal["key", "type"],
        text: str | None
    ) -> ToolResult:
        """Handle keyboard input actions.
        
        Args:
            action: The type of text input ("key" or "type")
            text: The text to type or key command to send
            
        Raises:
            ToolError: If text is invalid or missing
        """
        if text is None:
            logger.error(f"text is required for {action}")
            raise ToolError(f"text is required for {action}")

        if action == "key":
            logger.info(f"Executing key action: {text}")
            return self.shell(f"cliclick kp:{text}")
        else:  # type action
            logger.info(f"Executing type action: {text}")
            chunks = [text[i:i + TYPING_GROUP_SIZE] 
                     for i in range(0, len(text), TYPING_GROUP_SIZE)]
            
            result = None
            for chunk in chunks:
                result = self.shell(f"cliclick t:{shlex.quote(chunk)}")
                if len(chunks) > 1:
                    time.sleep(TYPING_DELAY_MS / 1000)
            return result or ToolResult(output=None, error=None)

    def screenshot(self):
        """Take and process a screenshot with proper scaling"""
        try:
            timestamp = datetime.now().strftime('%H_%M_%S')
            
            original_path = self.history_tracker.screenshots_dir / f"{timestamp}__1.png"
            scaled_path = self.history_tracker.screenshots_dir / f"{timestamp}__2.png"
            final_path = self.history_tracker.screenshots_dir / f"{timestamp}__3.png"

            screenshot_cmd = f"screencapture -x {shlex.quote(str(original_path))}"
            result = self.shell(screenshot_cmd, take_screenshot=False)

            if not original_path.exists():
                logger.error(f"Failed to take screenshot: {result.error}")
                raise ToolError(f"Failed to take screenshot: {result.error}")
            logger.info(f"took screenshot to {original_path}, dimensions {self.width}x{self.height}")

            scaled_width, scaled_height = self.scale_coordinates(
                ScalingSource.COMPUTER, 
                self.width, 
                self.height
            )
            scale_cmd = (
                f"sips -z {scaled_height} {scaled_width} "
                f"{shlex.quote(str(original_path))} "
                f"--out {shlex.quote(str(scaled_path))}"
            )
            self.shell(scale_cmd, take_screenshot=False)
            if not scaled_path.exists():
                logger.error(f"Failed to scale screenshot: {result.error}")
                raise ToolError(f"Failed to scale screenshot: {result.error}")
            logger.info(f"scaled screenshot to {scaled_path} with dimensions {scaled_width}x{scaled_height}")

            optimize_cmd = (
                f"pngquant '{SCREENSHOT_COLOR_DEPTH}' "
                f"--quality=0-85 --speed 1 --force "
                f"--output {shlex.quote(str(final_path))} "
                f"{shlex.quote(str(scaled_path))}"
            )
            optimize_result = self.shell(optimize_cmd, take_screenshot=False)
            
            if not final_path.exists():
                logger.error(f"Failed to optimize screenshot: {optimize_result.error}")
                raise ToolError(f"pngquant failed to process image: {optimize_result.error}")
            logger.info(f"optimized screenshot to {final_path}, dimensions {scaled_width}x{scaled_height}")

            processed_bytes = final_path.read_bytes()
            return result.replace(
                base64_image=base64.b64encode(processed_bytes).decode()
            )

        finally:
            if not KEEP_SCREENSHOTS:
                for path in (original_path, scaled_path, final_path):
                    if path.exists():
                        path.unlink()

    def shell(self, command: str, take_screenshot=True) -> ToolResult:
        """Run a shell command and return the output, error, and optionally a screenshot."""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            stdout = result.stdout
            stderr = result.stderr
            base64_image = None

            if result.returncode != 0:
                logger.error(f"Failed to execute command {command}: {stderr}")
                raise ToolError(stderr)
            return ToolResult(
                output=stdout or None,
                error=stderr or None,
                base64_image=base64_image
            )
        except Exception as e:
            logger.error(f"Failed to execute command {command}: {e}")
            raise ToolError(str(e))

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
            logger.info(f"scaling mouse move to {x},{y} from {coordinate[0]},{coordinate[1]}")
            command = f"cliclick m:{x},{y}"
            logger.info(f"Executing command: {command}")
            return self.shell(command)

    def get_cursor_position(self, coordinate: tuple[int, int] | None = None, text: str | None = None) -> ToolResult:
        """Get the current cursor position."""
        logger.info("Executing cursor_position")
        if coordinate is not None:
            logger.error("coordinate is not accepted for cursor_position")
            raise ToolError("coordinate is not accepted for cursor_position")
        if text is not None:
            raise ToolError("text is not accepted for cursor_position")

        result = self.shell("cliclick p", take_screenshot=False)
        
        if result.output:
            try:
                x, y = map(int, result.output.strip().split(','))
                scaled_x, scaled_y = self.scale_coordinates(ScalingSource.COMPUTER, x, y)
                logger.info(f"scaled cursor position to {scaled_x},{scaled_y} from {x},{y}")
                return result.replace(output=f"X={scaled_x},Y={scaled_y}")
            except ValueError:
                logger.error(f"Failed to parse cursor position from: {result.output}")
                raise ToolError(f"Failed to parse cursor position from: {result.output}")
        
        logger.error("Failed to get cursor position")
        raise ToolError("Failed to get cursor position")

def get_screen_dimensions():
    """Get the main display dimensions on macOS.
    
    Returns:
        tuple[int, int]: Width and height in pixels, or (0, 0) if detection fails
    """
    logger.info("Getting screen dimensions")
    try:
        # Using system_profiler which is native to macOS
        output = subprocess.check_output(
            ['system_profiler', 'SPDisplaysDataType'], 
            text=True
        )
        
        # Look for the main display resolution
        match = re.search(r'Resolution: (\d+) x (\d+)', output)
        if match:
            width = int(match.group(1))
            height = int(match.group(2))
            logger.info(f"Detected screen dimensions: {width}x{height}")
            return width, height
            
        logger.warning("Could not parse screen dimensions from system_profiler output")
        return 0, 0
        
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to execute system_profiler: {e}")
        return 0, 0
    except Exception as e:
        logger.error(f"Unexpected error getting screen dimensions: {e}")
        return 0, 0

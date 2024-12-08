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
import io

from anthropic.types.beta import BetaToolComputerUse20241022Param

from .base import BaseAnthropicTool, ToolError, ToolResult
from .run import run
from compass.constants import SCREENSHOT_SCALE_FACTOR, SCALING_ENABLED
from compass.utils.utility import HistoryLogger
from .computer_actions.screenshot import ScreenshotAction
from .computer_actions.cursor_position import CursorPositionAction
from .computer_actions.mouse_movement import MouseMovementAction
from .computer_actions.mouse_click import MouseClickAction
from .computer_actions.keyboard_input import KeyboardInputAction

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
 
        # Common parameters for all actions
        action_params = {
            "width": self.width,
            "height": self.height,
            "scaled_width": self.scaled_width,
            "scaled_height": self.scaled_height
        }
        
        # Initialize all actions with common parameters
        self.screenshot_action = ScreenshotAction(**action_params)
        self.cursor_position_action = CursorPositionAction(**action_params)
        self.mouse_movement_action = MouseMovementAction(**action_params)
        self.mouse_click_action = MouseClickAction(**action_params)
        self.keyboard_input_action = KeyboardInputAction(**action_params)

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
            return self.screenshot_action.execute()
        elif action in ("left_click", "right_click"):
            return self.mouse_click_action.execute(action=action, coordinate=coordinate)
        elif action in ("key", "type"):
            return self.keyboard_input_action.execute(action=action, text=text)
        elif action == "mouse_move":
            return self.mouse_movement_action.execute(coordinate=coordinate)
        elif action == "cursor_position":
            return self.cursor_position_action.execute(coordinate=coordinate, text=text)
        else:
            raise ToolError(f"Action '{action}' is not implemented yet.")

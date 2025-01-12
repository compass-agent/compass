import pyautogui
from typing import Literal, TypedDict
import logging
from enum import StrEnum
from compass.services.state_manager import StateManager
from anthropic.types.beta import BetaToolComputerUse20241022Param

from ..base import BaseAnthropicTool, ToolError
from compass.constants import SCREENSHOT_SCALE_FACTOR
from .screenshot import ScreenshotAction
from .cursor_position import CursorPositionAction
from .mouse_movement import MouseMovementAction
from .mouse_click import MouseClickAction
from .keyboard_input import KeyboardInputAction

logger = logging.getLogger(__name__)

Action = Literal[
    "screenshot",
    "left_click",
    "right_click",
    "middle_click",
    "double_click",
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

    _scaling_factor = SCREENSHOT_SCALE_FACTOR

    @property
    def options(self) -> ComputerToolOptions:
        return {
            "display_width_px": self.scaled_width, 
            "display_height_px": self.scaled_height,
        }

    def to_params(self) -> BetaToolComputerUse20241022Param:
        return {"name": self.name, "type": self.api_type, **self.options}

    def __init__(self, state_manager: StateManager):
        super().__init__()
        logger.info("Initializing ComputerTool")
        self._initialize_screen_dimensions()
        logger.info("Finding best target dimension, XGA, WXGA, FWXGA...")
        self._find_best_standard_dimension()
                # Broadcast scaling factors to frontend
        state_manager.broadcast_scaling_factors(
            x_factor=self._x_scaling_factor,
            y_factor=self._y_scaling_factor
        )
        logger.info(f"Computer works with image dimensions of {self.width}x{self.height}")
        logger.info(f"Agent will be working with image dimensions of {self.scaled_width}x{self.scaled_height}")
        
        # Common parameters for all actions
        action_params = {
            "width": self.width,
            "height": self.height,
            "scaled_width": self.scaled_width,
            "scaled_height": self.scaled_height,
            "state_manager": state_manager,
        }
        
        # Initialize actions with specific settings
        self.screenshot_action = ScreenshotAction(**action_params)
        self.cursor_position_action = CursorPositionAction(**action_params)
        self.mouse_movement_action = MouseMovementAction(**action_params)
        self.mouse_click_action = MouseClickAction(**action_params)
        self.keyboard_input_action = KeyboardInputAction(**action_params)

    def _initialize_screen_dimensions(self) -> None:
        """Initialize screen dimensions using pyautogui."""
        self.width, self.height = pyautogui.size()
        logger.info(f"Original dimensions: {self.width}, {self.height}")
        
        if not (self.width and self.height):
            logger.error("Could not determine screen dimensions, thus quitting") 
            raise ToolError("Could not determine screen dimensions")

    def _find_best_standard_dimension(self) -> None:
        """
        Find the best matching standard resolution based on aspect ratio.
        """
        ratio = self.width / self.height
        logger.info(f"checking for best standard dimension that matches aspect ratio of {ratio}")
        
        base_x_scale = base_y_scale = 1
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

    async def __call__(
        self,
        *,
        action: Action,
        text: str | None = None,
        coordinate: tuple[int, int] | None = None,
        **kwargs,
    ):
        if action == "screenshot":
            return await self.screenshot_action.execute()
        elif action in ("left_click", "right_click", "middle_click", "double_click"):
            return await self.mouse_click_action.execute(action=action, coordinate=coordinate)
        elif action in ("key", "type"):
            return await self.keyboard_input_action.execute(action=action, text=text)
        elif action == "mouse_move":
            return await self.mouse_movement_action.execute(coordinate=coordinate)
        elif action == "cursor_position":
            return await self.cursor_position_action.execute(coordinate=coordinate, text=text)
        else:
            raise ToolError(f"Action '{action}' is not implemented yet.")

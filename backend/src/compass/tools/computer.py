import asyncio
import base64
import os
import shlex
from pathlib import Path
from typing import Literal, TypedDict
from uuid import uuid4

from anthropic.types.beta import BetaToolComputerUse20241022Param

from .base import BaseAnthropicTool, ToolError, ToolResult
from .run import run

OUTPUT_DIR = "/tmp/outputs"

Action = Literal[
    "screenshot",
    "left_click",
    "right_click",
    # Remaining placeholders
    # "key",
    # "type",
    # "mouse_move",
    # "left_click_drag",
    # "middle_click",
    # "double_click",
    # "cursor_position",
]

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

    @property
    def options(self) -> ComputerToolOptions:
        return {
            "display_width_px": self.width,
            "display_height_px": self.height,
        }

    def to_params(self) -> BetaToolComputerUse20241022Param:
        return {"name": self.name, "type": self.api_type, **self.options}

    def __init__(self):
        super().__init__()

        self.width = int(os.getenv("WIDTH") or 0)
        self.height = int(os.getenv("HEIGHT") or 0)
        assert self.width and self.height, "WIDTH and HEIGHT must be set"

    async def __call__(
        self,
        *,
        action: Action,
        coordinate: tuple[int, int] | None = None,
        **kwargs,
    ):
        if action == "screenshot":
            return await self.screenshot()
        elif action in ("left_click", "right_click"):
            return await self.handle_click(action, coordinate)
        else:
            # Placeholder for other actions
            raise ToolError(f"Action '{action}' is not implemented yet.")

    async def handle_click(
        self, 
        action: Literal["left_click", "right_click"], 
        coordinate: tuple[int, int] | None
    ) -> ToolResult:
        """Handle mouse click actions.
        
        Args:
            action: The type of click action ("left_click" or "right_click")
            coordinate: A tuple of (x, y) coordinates where to click
            
        Raises:
            ToolError: If coordinates are invalid or out of bounds
        """
        if coordinate is None:
            raise ToolError(f"coordinate is required for {action}")
        if not isinstance(coordinate, (list, tuple)) or len(coordinate) != 2:
            raise ToolError(f"{coordinate} must be a tuple of length 2")
        if not all(isinstance(i, int) and i >= 0 for i in coordinate):
            raise ToolError(f"{coordinate} must be a tuple of non-negative ints")
        
        x, y = coordinate
        if x > self.width or y > self.height:
            raise ToolError(f"Coordinates {x}, {y} are out of bounds")
            
        click_type = "c" if action == "left_click" else "rc"
        return await self.shell(f"cliclick {click_type}:{x},{y}")

    async def screenshot(self):
        """Take a screenshot of the current screen on MacOS and return the base64 encoded image."""
        output_dir = Path(OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"screenshot_{uuid4().hex}.png"

        screenshot_cmd = f"screencapture -x {shlex.quote(str(path))}"
        result = await self.shell(screenshot_cmd, take_screenshot=False)

        if path.exists():
            return result.replace(
                base64_image=base64.b64encode(path.read_bytes()).decode()
            )
        raise ToolError(f"Failed to take screenshot: {result.error}")

    async def shell(self, command: str, take_screenshot=True) -> ToolResult:
        """Run a shell command and return the output, error, and optionally a screenshot."""
        _, stdout, stderr = await run(command)
        base64_image = None

        return ToolResult(
            output=stdout or None,  
            error=stderr or None,  # Convert empty string to None
            base64_image=base64_image
        )

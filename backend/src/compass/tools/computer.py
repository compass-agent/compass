import subprocess
import base64
import os
import shlex
from pathlib import Path
from typing import Literal, TypedDict
from uuid import uuid4
import re
import logging

from anthropic.types.beta import BetaToolComputerUse20241022Param

from .base import BaseAnthropicTool, ToolError, ToolResult
from .run import run

OUTPUT_DIR = "/tmp/outputs"

logger = logging.getLogger(__name__)

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
        
        # Try environment variables first
        self.width = int(os.getenv("WIDTH") or 0)
        self.height = int(os.getenv("HEIGHT") or 0)
        
        # If not set via environment, detect from system
        if not (self.width and self.height):
            self.width, self.height = get_screen_dimensions()
        
        # Validate we have valid dimensions
        if not (self.width and self.height):
            raise ToolError("Could not determine screen dimensions")

    def __call__(
        self,
        *,
        action: Action,
        coordinate: tuple[int, int] | None = None,
        **kwargs,
    ):
        if action == "screenshot":
            return self.screenshot()
        elif action in ("left_click", "right_click"):
            return self.handle_click(action, coordinate)
        else:
            # Placeholder for other actions
            raise ToolError(f"Action '{action}' is not implemented yet.")

    def handle_click(
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
        return self.shell(f"cliclick {click_type}:{x},{y}")

    def screenshot(self):
        """Take a screenshot of the current screen on MacOS and return the base64 encoded image."""
        output_dir = Path(OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"screenshot_{uuid4().hex}.png"

        screenshot_cmd = f"screencapture -x {shlex.quote(str(path))}"
        result = self.shell(screenshot_cmd, take_screenshot=False)

        if path.exists():
            return result.replace(
                base64_image=base64.b64encode(path.read_bytes()).decode()
            )
        raise ToolError(f"Failed to take screenshot: {result.error}")

    def shell(self, command: str, take_screenshot=True) -> ToolResult:
        """Run a shell command and return the output, error, and optionally a screenshot."""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            stdout = result.stdout
            stderr = result.stderr
            base64_image = None

            if result.returncode != 0:
                raise ToolError(stderr)

            return ToolResult(
                output=stdout or None,
                error=stderr or None,
                base64_image=base64_image
            )
        except Exception as e:
            raise ToolError(str(e))

def get_screen_dimensions():
    """Get the main display dimensions on macOS.
    
    Returns:
        tuple[int, int]: Width and height in pixels, or (0, 0) if detection fails
    """
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

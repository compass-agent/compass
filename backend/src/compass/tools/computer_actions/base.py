from abc import ABC, abstractmethod
from typing import Any
from ..base import ToolResult, ScalingSource, ToolError
import logging

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
    def execute(self, **kwargs) -> ToolResult:
        """Execute the computer action."""
        pass 
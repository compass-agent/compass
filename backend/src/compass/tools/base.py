from abc import ABCMeta, abstractmethod
from typing import Any, Dict
from compass.types.agent import ToolResult
class BaseTool(metaclass=ABCMeta):

    @abstractmethod
    async def __call__(self, **kwargs) -> Any:
        """Executes the tool with the given arguments."""
        ...

    @abstractmethod
    def to_params(
        self,
    ) -> Dict[str, Any]:
        raise NotImplementedError



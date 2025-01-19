from abc import ABC, abstractmethod
from compass.constants import PROMPT_CACHING
from compass.types.agent import SystemMessage

class BasePrompt(ABC):
    @abstractmethod
    def get_manual_mode_highlight_off_prompt(self) -> SystemMessage:
        pass

    @abstractmethod
    def get_tool_mode_prompt(self) -> SystemMessage:
        pass

    def get_system_prompt(self, manual_mode: bool = True, highlight_mode: bool = False) -> SystemMessage:
        """Returns the appropriate system prompt based on the highlight mode"""
        if manual_mode:
            if not highlight_mode:
                system_prompt = self.get_manual_mode_highlight_off_prompt()
            else:
                raise NotImplementedError("Highlight mode is not yet supported")
        else:
            if highlight_mode:
                raise ValueError("Highlight mode cannot be active in auto mode")
            else:
                system_prompt = self.get_tool_mode_prompt()

        return system_prompt
import logging
from typing import Any, Dict, List, Optional
from compass.constants import LLM_PROVIDER
from compass.llm.base import BaseLLMInterface
from compass.llm.anthropic_llm import AnthropicLLM
from compass.llm.google_llm import GoogleLLM
from compass.llm.memory_management import MemoryManager
from ..types.agent import SystemMessage

logger = logging.getLogger(__name__)

class LLMFactory:
    @staticmethod
    def create_llm(
        memory_manager: MemoryManager, 
        tools_params: List[Dict[str, Any]], 
        manual_system_message: SystemMessage,
        auto_system_message: SystemMessage
    ) -> BaseLLMInterface:
        """
        Factory method to create the appropriate LLM instance based on configuration
        """
        providers = {
            "google": GoogleLLM,
            "anthropic": AnthropicLLM
        }
        
        llm_class = providers.get(LLM_PROVIDER.lower(), AnthropicLLM)
        
        try:
            return llm_class(
                memory_manager=memory_manager, 
                tools_params=tools_params, 
                manual_system_message=manual_system_message,
                auto_system_message=auto_system_message
            )
        except ValueError as e:
            logger.error(f"Failed to initialize {LLM_PROVIDER} LLM: {e}")
            raise RuntimeError(
                f"Cannot initialize LLM provider '{LLM_PROVIDER}': {e}"
            ) from e

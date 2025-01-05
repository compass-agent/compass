from .base import BasePrompt
from .generic_prompt import GenericPrompt
from .openfoam_prompt import OpenFoamPrompt

def get_prompt_handler(agent_name: str) -> BasePrompt:
    if agent_name == "OpenFoam":
        return OpenFoamPrompt()
    elif agent_name == "Generic":
        return GenericPrompt()
    else:
        raise ValueError(f"Unknown agent name: {agent_name}") 
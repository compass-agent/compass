from .base import BasePrompt
from .generic_prompt import GenericPrompt
from .openfoam_prompt import OpenFoamPrompt
from .FreeCAD_prompt import FreeCADPrompt

def get_prompt_handler(agent_name: str) -> BasePrompt:
    if agent_name == "OpenFoam":
        return OpenFoamPrompt()
    elif agent_name == "Generic":
        return GenericPrompt()
    elif agent_name == "FreeCAD":
        return FreeCADPrompt()
    else:
        raise ValueError(f"Unknown agent name: {agent_name}") 

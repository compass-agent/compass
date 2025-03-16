from typing import Dict, Optional, Type
from .base import BasePrompt
from .generic_prompt import GenericPrompt
from .openfoam_prompt import OpenFoamPrompt
from .FreeCAD_prompt import FreeCADPrompt
from .structural_engineer_prompt import StructuralEngineerPrompt

# Map of agent names to prompt classes
PROMPT_MAP: Dict[str, Type[BasePrompt]] = {
    "Generic": GenericPrompt,
    "OpenFoam": OpenFoamPrompt,
    "FreeCAD": FreeCADPrompt,
    "structural-engineer": StructuralEngineerPrompt
}

def get_prompt_handler(agent_type: Optional[str] = None) -> BasePrompt:
    """Get the prompt handler for the specified agent type."""
    if agent_type is None:
        agent_type = "Generic"
    
    prompt_class = PROMPT_MAP.get(agent_type)
    if prompt_class is None:
        prompt_class = GenericPrompt
    
    return prompt_class() 

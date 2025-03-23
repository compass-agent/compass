from abc import ABC, abstractmethod
import json
import os
from typing import Optional
from compass.constants import PROMPT_CACHING
from compass.types.agent import SystemMessage

class BasePrompt(ABC):
    @abstractmethod
    def get_manual_mode_prompt(self) -> SystemMessage:
        pass

    @abstractmethod
    def get_tool_mode_prompt(self) -> SystemMessage:
        pass

    def get_workflow_instruction(self, workflow_name: str) -> str:
        """Returns workflow instructions for a specific workflow"""
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cases_path = os.path.join(current_dir, 'workflows', 'cases.json')
        
        with open(cases_path, 'r') as f:
            cases = json.load(f)
            
        # Find the matching workflow
        workflow_case = next((case for case in cases if case['name'] == workflow_name), None)
        if not workflow_case:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        # Read the workflow content from the specified file
        workflow_file_path = os.path.join(current_dir, 'workflows', workflow_case['workflow_file_name'])
        with open(workflow_file_path, 'r') as f:
            workflow_content = f.read()
            
        return f"""
I am providing you with a specific workflow for the task:
{workflow_case['description']}

This workflow contains detailed step-by-step instructions that must be followed precisely. 
Please carefully execute each step in sequence until the task is completed.

Workflow details:
{workflow_content}
"""

    def get_system_prompt(self, manual_mode: bool = True, workflow_name: Optional[str] = None) -> SystemMessage:
        """Returns the appropriate system prompt based on mode and workflow"""
        if manual_mode:
            system_prompt = self.get_manual_mode_prompt()
        else:
            system_prompt = self.get_tool_mode_prompt()

        if workflow_name:
            workflow_instructions = self.get_workflow_instruction(workflow_name)
            system_prompt.content = f"{system_prompt.content}\n\n{workflow_instructions}"

        return system_prompt
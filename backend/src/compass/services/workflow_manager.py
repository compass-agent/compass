import json
import os
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class WorkflowManager:
    def __init__(self):
        self.workflows_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'agent', 
            'prompt', 
            'workflows', 
            'cases.json'
        )

    def get_workflow_names(self) -> List[str]:
        """
        Retrieve list of available workflow names from cases.json
        """
        try:
            with open(self.workflows_path, 'r') as f:
                workflows = json.load(f)
            return [workflow['name'] for workflow in workflows]
        except FileNotFoundError:
            logger.error(f"Workflow file not found at {self.workflows_path}")
            return []
        except json.JSONDecodeError:
            logger.error("Error parsing workflows JSON file")
            return []
        except Exception as e:
            logger.error(f"Unexpected error reading workflows: {str(e)}")
            return []

    def get_workflow_details(self) -> List[Dict]:
        """
        Retrieve full workflow details including name, description, and agent
        """
        try:
            with open(self.workflows_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading workflow details: {str(e)}")
            return []
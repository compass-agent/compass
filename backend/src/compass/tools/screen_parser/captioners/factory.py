import yaml
from pathlib import Path
from typing import Dict, Any
from .base import BaseCaptioner
from .claude_captioner import ClaudeCaptioner

class CaptionerFactory:
    @staticmethod
    def load_config() -> Dict[str, Any]:
        config_path = Path(__file__).parent.parent / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config['captioning']

    @staticmethod
    def create_captioner() -> BaseCaptioner:
        """
        Create a captioner instance based on configuration
        """
        # Load config
        config = CaptionerFactory.load_config()
        captioner_type = config['default']
        # Create appropriate captioner
        if captioner_type == 'claude':
            return ClaudeCaptioner()
        
        raise ValueError(f"Unknown captioner type: {captioner_type}") 
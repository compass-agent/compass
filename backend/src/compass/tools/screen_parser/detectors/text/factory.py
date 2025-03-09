import yaml
from pathlib import Path
from typing import Dict, Any
from .base import BaseTextDetector
from .google_detector import GoogleCloudTextDetector

class TextDetectorFactory:
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """Load text detection configuration from config file"""
        config_path = Path(__file__).parent.parent.parent / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config['text_detection']

    @staticmethod
    def create_detector() -> BaseTextDetector:
        """
        Create a text detector instance based on configuration.
        All detectors must implement BaseTextDetector and work with ScreenData.
        
        Returns:
            BaseTextDetector: Configured text detector instance
        
        Raises:
            ValueError: If configured detector type is unknown
        """
        config = TextDetectorFactory.load_config()
        detector_type = config['default']
        
        if detector_type == 'google':
            return GoogleCloudTextDetector()
        
        raise ValueError(f"Unknown detector type: {detector_type}") 
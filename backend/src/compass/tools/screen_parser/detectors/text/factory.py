import yaml
from pathlib import Path
from typing import Dict, Any
from .base import BaseTextDetector
from .paddle_detector import PaddleTextDetector
from .easyocr_detector import EasyOCRDetector
from .google_detector import GoogleCloudTextDetector

class TextDetectorFactory:
    @staticmethod
    def load_config() -> Dict[str, Any]:
        config_path = Path(__file__).parent.parent.parent / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config['text_detection']

    @staticmethod
    def create_detector() -> BaseTextDetector:
        """
        Create a text detector instance based on configuration
        """
        # Load config
        config = TextDetectorFactory.load_config()
        detector_type = config['default']
        # Create appropriate detector
        if detector_type == 'easyocr':
            return EasyOCRDetector()
        elif detector_type == 'paddle':
            return PaddleTextDetector()
        elif detector_type == 'google':
            return GoogleCloudTextDetector()
        
        raise ValueError(f"Unknown detector type: {detector_type}") 
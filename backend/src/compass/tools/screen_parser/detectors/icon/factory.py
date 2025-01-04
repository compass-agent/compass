import yaml
from pathlib import Path
from typing import Dict, Any
from .base import BaseIconDetector
from .yolo_detector import YOLOIconDetector

class IconDetectorFactory:
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """Load icon detection configuration from config file"""
        config_path = Path(__file__).parent.parent.parent / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config['icon_detection']

    @staticmethod
    def create_detector() -> BaseIconDetector:
        """
        Create an icon detector instance based on configuration.
        All detectors must implement BaseIconDetector and work with ScreenData.
        
        Returns:
            BaseIconDetector: Configured icon detector instance
        
        Raises:
            ValueError: If configured detector type is unknown
        """
        config = IconDetectorFactory.load_config()
        detector_type = config['default']
        
        if detector_type == 'yolo':
            return YOLOIconDetector()
        
        raise ValueError(f"Unknown detector type: {detector_type}") 
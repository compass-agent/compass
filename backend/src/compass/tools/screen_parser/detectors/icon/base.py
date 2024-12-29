from abc import ABC, abstractmethod
from .models import IconDetectionInput, IconDetectionOutput

class BaseIconDetector(ABC):
    """Abstract base class for icon detection"""
    
    @abstractmethod
    def __init__(self, model_path: str):
        """
        Initialize icon detector
        
        Args:
            model_path: Path to model weights/configuration
        """
        pass
    
    @abstractmethod
    def detect(self, input_data: IconDetectionInput) -> IconDetectionOutput:
        """
        Detect icons in the input image
        
        Args:
            input_data: IconDetectionInput object containing image and detection parameters
            
        Returns:
            IconDetectionOutput object containing detected icon locations
        """
        pass 
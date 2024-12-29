from abc import ABC, abstractmethod
from .models import TextDetectionInput, TextDetectionOutput

class BaseTextDetector(ABC):
    """Abstract base class for text detection"""
    
    @abstractmethod
    def detect(self, input_data: TextDetectionInput) -> TextDetectionOutput:
        """
        Detect text in the input image
        
        Args:
            input_data: TextDetectionInput object containing base64 encoded image
            
        Returns:
            TextDetectionOutput object containing detected texts and their locations
        """
        pass 
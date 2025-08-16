from abc import ABC, abstractmethod
from compass.tools.screen_parser.models import ScreenData

class BaseTextDetector(ABC):
    """Abstract base class for text detection"""
    
    @abstractmethod
    def detect(self, screen_data: ScreenData) -> ScreenData:
        """
        Detect text in the input image and return new ScreenData instance
        
        Args:
            screen_data: ScreenData object containing image and detection parameters
            
        Returns:
            New ScreenData object containing detected texts
        """
        pass 
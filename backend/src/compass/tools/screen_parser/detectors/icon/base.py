from abc import ABC, abstractmethod
from compass.tools.screen_parser.models import ScreenData

class BaseIconDetector(ABC):
    """Abstract base class for icon detection"""
    
    @abstractmethod
    def __init__(self):
        """Initialize icon detector"""
        pass
    
    @abstractmethod
    def detect(self, screen_data: ScreenData) -> ScreenData:
        """
        Detect icons in the input image and return new ScreenData instance
        
        Args:
            screen_data: ScreenData object containing image and detection parameters
            
        Returns:
            New ScreenData object containing detected icons
        """
        pass 
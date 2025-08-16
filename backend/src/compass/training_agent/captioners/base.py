from abc import ABC, abstractmethod
from compass.tools.screen_parser.models import ScreenData

class BaseCaptioner(ABC):
    """Abstract base class for image captioning"""
    
    @abstractmethod
    def __init__(self, **kwargs):
        """Initialize captioner with model-specific parameters"""
        pass
    
    @abstractmethod
    def generate_captions(self, screen_data: ScreenData) -> ScreenData:
        """
        Generate captions for icons in the screen data
        
        Args:
            screen_data: ScreenData object containing image and detected elements
            
        Returns:
            Updated ScreenData object with captions added to icon elements
        """
        pass 
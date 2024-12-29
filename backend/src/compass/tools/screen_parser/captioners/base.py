from abc import ABC, abstractmethod
from .models import CaptioningInput, CaptioningOutput

class BaseCaptioner(ABC):
    """Abstract base class for image captioning"""
    
    @abstractmethod
    def __init__(self, **kwargs):
        """Initialize captioner with model-specific parameters"""
        pass
    
    @abstractmethod
    def generate_captions(self, input_data: CaptioningInput) -> CaptioningOutput:
        """
        Generate captions for image regions
        
        Args:
            input_data: CaptioningInput object containing image and regions
            
        Returns:
            CaptioningOutput object containing generated captions
        """
        pass 
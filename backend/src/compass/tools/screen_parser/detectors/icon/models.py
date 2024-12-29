from dataclasses import dataclass
from typing import List, Tuple, Optional
import base64
from PIL import Image
import io
import numpy as np

@dataclass
class IconBox:
    """Represents a detected icon region with its location and confidence"""
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    confidence: float
    
    @property
    def coordinates(self) -> dict:
        return {
            'x1': self.bbox[0],
            'y1': self.bbox[1],
            'x2': self.bbox[2],
            'y2': self.bbox[3]
        }

@dataclass
class IconDetectionInput:
    """Input for icon detection"""
    image_data: str  # base64 encoded image
    image_size: Optional[Tuple[int, int]] = None  # Optional target size (height, width)
    
    @classmethod
    def from_base64(cls, base64_string: str, **kwargs) -> 'IconDetectionInput':
        """Create input from base64 encoded image"""
        return cls(
            image_data=base64_string,
            **kwargs
        )
    
    @classmethod
    def from_path(cls, image_path: str, **kwargs) -> 'IconDetectionInput':
        """Create input from image path"""
        with open(image_path, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            
        # Get image size from the file
        with Image.open(image_path) as img:
            width, height = img.size
            image_size = (height, width)
            
        return cls(
            image_data=encoded_string,
            image_size=image_size,
            **kwargs
        )
    
    def to_pil(self) -> Image.Image:
        """Convert base64 to PIL Image"""
        image_bytes = base64.b64decode(self.image_data)
        return Image.open(io.BytesIO(image_bytes))
    
    def to_numpy(self) -> np.ndarray:
        """Convert base64 to numpy array"""
        return np.array(self.to_pil())

@dataclass
class IconDetectionOutput:
    """Output from icon detection"""
    boxes: List[IconBox]
    
    @property
    def bboxes(self) -> List[Tuple[float, float, float, float]]:
        """Get list of bounding boxes"""
        return [box.bbox for box in self.boxes]
    
    @property
    def confidences(self) -> List[float]:
        """Get list of confidence scores"""
        return [box.confidence for box in self.boxes] 
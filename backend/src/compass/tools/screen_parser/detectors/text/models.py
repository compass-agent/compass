from dataclasses import dataclass
from typing import List, Tuple, Optional
import base64
from PIL import Image
import io

@dataclass
class TextDetectionBox:
    """Represents a detected text region with its content and location"""
    text: str
    confidence: float
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    
    @property
    def coordinates(self) -> dict:
        return {
            'x1': self.bbox[0],
            'y1': self.bbox[1],
            'x2': self.bbox[2],
            'y2': self.bbox[3]
        }

@dataclass
class TextDetectionInput:
    """Input for text detection"""
    image_data: str  # base64 encoded image
    
    @classmethod
    def from_base64(cls, base64_string: str) -> 'TextDetectionInput':
        """Create input from base64 encoded image"""
        return cls(image_data=base64_string)
    
    @classmethod
    def from_path(cls, image_path: str) -> 'TextDetectionInput':
        """Create input from image path"""
        with open(image_path, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return cls(image_data=encoded_string)
    
    def get_base64(self) -> str:
        """Get base64 string directly"""
        return self.image_data
    
    def to_pil(self) -> Image.Image:
        """Convert base64 to PIL Image if needed"""
        image_bytes = base64.b64decode(self.image_data)
        return Image.open(io.BytesIO(image_bytes))

@dataclass
class TextDetectionOutput:
    """Output from text detection"""
    boxes: List[TextDetectionBox]
    
    @property
    def texts(self) -> List[str]:
        """Get list of detected texts"""
        return [box.text for box in self.boxes]
    
    @property
    def bboxes(self) -> List[Tuple[float, float, float, float]]:
        """Get list of bounding boxes"""
        return [box.bbox for box in self.boxes] 
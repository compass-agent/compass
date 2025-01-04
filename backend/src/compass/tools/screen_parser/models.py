from dataclasses import dataclass
from typing import List, Tuple, Optional, Literal
from PIL import Image
import base64
import io
import numpy as np

@dataclass
class BoundingBox:
    """Unified bounding box representation for all screen elements"""
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    element_type: Literal["text", "icon"]
    confidence: float
    text: Optional[str] = None  # For text elements
    caption: Optional[str] = None  # For icon elements
    
    @property
    def coordinates(self) -> dict:
        return {
            'x1': self.bbox[0],
            'y1': self.bbox[1],
            'x2': self.bbox[2],
            'y2': self.bbox[3]
        }

@dataclass
class ScreenData:
    """Unified representation of a screen and its elements"""
    image_data: str  # base64 encoded image
    elements: List[BoundingBox] = None
    description: Optional[str] = None  # New field for screen description
    
    def __post_init__(self):
        self.elements = self.elements or []
    
    @classmethod
    def from_base64(cls, base64_string: str) -> 'ScreenData':
        return cls(image_data=base64_string)
    
    @classmethod
    def from_path(cls, image_path: str) -> 'ScreenData':
        with open(image_path, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return cls(image_data=encoded_string)
    
    def to_pil(self) -> Image.Image:
        """Convert base64 to PIL Image"""
        image_bytes = base64.b64decode(self.image_data)
        return Image.open(io.BytesIO(image_bytes))
    
    def to_numpy(self) -> np.ndarray:
        """Convert base64 to numpy array"""
        pil_image = self.to_pil()
        # Convert to numpy array while explicitly preserving RGB format
        return np.asarray(pil_image, dtype=np.uint8)
    
    def add_text_element(self, bbox: Tuple[float, float, float, float], 
                        text: str, confidence: float) -> None:
        """Add a text element"""
        self.elements.append(BoundingBox(
            bbox=bbox,
            element_type="text",
            confidence=confidence,
            text=text
        ))
    
    def add_icon_element(self, bbox: Tuple[float, float, float, float],
                        confidence: float, caption: Optional[str] = None) -> None:
        """Add an icon element"""
        self.elements.append(BoundingBox(
            bbox=bbox,
            element_type="icon",
            confidence=confidence,
            caption=caption
        ))
    
    @property
    def text_elements(self) -> List[BoundingBox]:
        """Get all text elements"""
        return [e for e in self.elements if e.element_type == "text"]
    
    @property
    def icon_elements(self) -> List[BoundingBox]:
        """Get all icon elements"""
        return [e for e in self.elements if e.element_type == "icon"] 
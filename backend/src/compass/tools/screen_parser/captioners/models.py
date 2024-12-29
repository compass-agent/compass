from dataclasses import dataclass
from typing import List, Tuple, Optional, Union
import numpy as np
from PIL import Image
import base64
from io import BytesIO

@dataclass
class CaptioningInput:
    """Input for image captioning"""
    image: np.ndarray
    boxes: List[Tuple[float, float, float, float]]  # xyxy format
    prompt: Optional[str] = None
    batch_size: int = 32
    
    @classmethod
    def from_pil(cls, image: Image.Image, **kwargs) -> 'CaptioningInput':
        """Create input from PIL Image"""
        return cls(image=np.array(image), **kwargs)
    
    def get_crops(self) -> List[Image.Image]:
        """Get cropped images for each box"""
        crops = []
        for box in self.boxes:
            xmin, ymin, xmax, ymax = [int(coord) for coord in box]
            crop = Image.fromarray(self.image[ymin:ymax, xmin:xmax])
            crops.append(crop)
        return crops

@dataclass
class CaptioningOutput:
    """Output from image captioning"""
    captions: List[str]
    metadata: Optional[dict] = None 
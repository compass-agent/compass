import easyocr
import numpy as np
from .base import BaseTextDetector
from .models import TextDetectionInput, TextDetectionOutput, TextDetectionBox

class EasyOCRDetector(BaseTextDetector):
    def __init__(self):
        self.detector = easyocr.Reader(['en'])
    
    def detect(self, input_data: TextDetectionInput) -> TextDetectionOutput:
        # Convert base64 to PIL Image
        image = input_data.to_pil()
        
        # Convert PIL Image to numpy array
        image_array = np.array(image)
        
        # Run detection
        result = self.detector.readtext(image_array)
        
        # Process results
        boxes = []
        for coords, text, confidence in result:
            # Convert to XYXY format
            x1 = coords[0][0]
            y1 = coords[0][1]
            x2 = coords[2][0]
            y2 = coords[2][1]
            
            boxes.append(TextDetectionBox(
                text=text,
                confidence=confidence,
                bbox=(x1, y1, x2, y2)
            ))
        
        return TextDetectionOutput(boxes=boxes) 
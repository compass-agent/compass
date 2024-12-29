from paddleocr import PaddleOCR
from .base import BaseTextDetector
from .models import TextDetectionInput, TextDetectionOutput, TextDetectionBox
import numpy as np

class PaddleTextDetector(BaseTextDetector):
    def __init__(self):
        self.detector = PaddleOCR(
            lang='en',
            use_angle_cls=False,
            use_gpu=False,
            show_log=True,
            max_batch_size=32,
            use_dilation=True,
            det_db_score_mode='fast',
            rec_batch_num=32
        )
    
    def detect(self, input_data: TextDetectionInput) -> TextDetectionOutput:
        # Convert base64 to PIL Image
        image = input_data.to_pil()
        
        # Convert PIL Image to numpy array
        image_array = np.array(image)
        
        # Run detection
        result = self.detector.ocr(image_array, cls=False)[0]
        
        # Process results
        boxes = []
        if result is not None:
            for item in result:
                coords = item[0]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                text = item[1][0]  # text content
                confidence = item[1][1]  # confidence score
                
                # Convert to XYXY format
                x1 = min(point[0] for point in coords)
                y1 = min(point[1] for point in coords)
                x2 = max(point[0] for point in coords)
                y2 = max(point[1] for point in coords)
                
                boxes.append(TextDetectionBox(
                    text=text,
                    confidence=confidence,
                    bbox=(x1, y1, x2, y2)
                ))
        
        return TextDetectionOutput(boxes=boxes) 
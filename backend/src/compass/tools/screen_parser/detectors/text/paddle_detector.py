from paddleocr import PaddleOCR
from .base import BaseTextDetector
from compass.tools.screen_parser.models import ScreenData
import numpy as np
import logging
import time

class PaddleTextDetector(BaseTextDetector):
    def __init__(self):
        """Initialize PaddleOCR detector"""
        self.logger = logging.getLogger("paddle_detector")
        self.logger.setLevel(logging.INFO)
        
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
        self.logger.info("PaddleOCR initialized")
    
    def detect(self, screen_data: ScreenData) -> ScreenData:
        """
        Detect text using PaddleOCR and return new ScreenData instance
        """
        detect_start = time.time()
        
        # Create new ScreenData instance for results
        result_screen = ScreenData(image_data=screen_data.image_data)
        
        # Convert to numpy array for PaddleOCR
        image_array = screen_data.to_numpy()
        
        # Run detection
        model_start = time.time()
        result = self.detector.ocr(image_array, cls=False)[0]
        model_time = time.time() - model_start
        self.logger.info(f"PaddleOCR detection took {model_time:.2f} seconds")
        
        # Process results
        process_start = time.time()
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
                
                result_screen.add_text_element(
                    bbox=(float(x1), float(y1), float(x2), float(y2)),
                    text=text,
                    confidence=float(confidence)
                )
        
        process_time = time.time() - process_start
        self.logger.info(f"Results processing took {process_time:.2f} seconds")
        
        total_time = time.time() - detect_start
        self.logger.info(f"Total detection time: {total_time:.2f} seconds")
        
        return result_screen 
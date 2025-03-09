import easyocr
import numpy as np
from .base import BaseTextDetector
from compass.tools.screen_parser.models import ScreenData
import logging
import time

class EasyOCRDetector(BaseTextDetector):
    def __init__(self):
        """Initialize EasyOCR detector"""
        self.logger = logging.getLogger("easyocr_detector")
        self.logger.setLevel(logging.INFO)
        
        self.detector = easyocr.Reader(['en'])
        self.logger.info("EasyOCR initialized")
    
    def detect(self, screen_data: ScreenData) -> ScreenData:
        """
        Detect text using EasyOCR and return new ScreenData instance
        """
        detect_start = time.time()
        
        # Create new ScreenData instance for results
        result_screen = ScreenData(image_data=screen_data.image_data)
        
        # Convert to numpy array for EasyOCR
        image_array = screen_data.to_numpy()
        
        # Run detection
        model_start = time.time()
        result = self.detector.readtext(image_array)
        model_time = time.time() - model_start
        self.logger.info(f"EasyOCR detection took {model_time:.2f} seconds")
        
        # Process results
        process_start = time.time()
        for coords, text, confidence in result:
            # Convert to XYXY format
            x1 = coords[0][0]
            y1 = coords[0][1]
            x2 = coords[2][0]
            y2 = coords[2][1]
            
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
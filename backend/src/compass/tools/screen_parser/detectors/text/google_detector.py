from google.cloud import vision
from .base import BaseTextDetector
from compass.tools.screen_parser.models import ScreenData
import base64
import logging
import time

class GoogleCloudTextDetector(BaseTextDetector):
    """Text detector implementation using Google Cloud Vision API"""
    
    def __init__(self):
        """Initialize the Google Cloud Vision client"""
        self.logger = logging.getLogger("google_detector")
        self.logger.setLevel(logging.INFO)
        self.client = vision.ImageAnnotatorClient()
    
    def detect(self, screen_data: ScreenData) -> ScreenData:
        """
        Detect text using Google Cloud Vision API
        """
        detect_start = time.time()
        
        # Create new ScreenData instance for results
        result_screen = ScreenData(image_data=screen_data.image_data)
        
        # Create image object from base64
        self.logger.info("Creating Vision API request")
        image = vision.Image(content=base64.b64decode(screen_data.image_data))
        
        # Perform text detection
        api_start = time.time()
        response = self.client.text_detection(image=image) # type: ignore
        api_time = time.time() - api_start
        self.logger.info(f"Google API call took {api_time:.2f} seconds")
        
        # Handle potential API errors
        if response.error.message:
            raise Exception(
                f"Error detecting text: {response.error.message}\n"
                "For more info on error messages, check: "
                "https://cloud.google.com/apis/design/errors"
            )
        
        # Process detected texts
        process_start = time.time()
        for text in response.text_annotations[1:]:  # Skip first result which is the entire text
            vertices = text.bounding_poly.vertices
            x1 = min(vertex.x for vertex in vertices)
            y1 = min(vertex.y for vertex in vertices)
            x2 = max(vertex.x for vertex in vertices)
            y2 = max(vertex.y for vertex in vertices)
            
            result_screen.add_text_element(
                bbox=(float(x1), float(y1), float(x2), float(y2)),
                text=text.description,
                confidence=1.0  # Google Cloud Vision doesn't provide confidence scores
            )
        
        process_time = time.time() - process_start
        self.logger.info(f"Results processing took {process_time:.2f} seconds")
        
        total_time = time.time() - detect_start
        self.logger.info(f"Total text detection time: {total_time:.2f} seconds")
        
        return result_screen 
import logging
from pathlib import Path
import pandas as pd
import base64
from typing import Dict, List, Tuple
import numpy as np
import cv2
from compass.tools.screen_parser.detectors.icon.yolo_detector import YOLOIconDetector
from compass.tools.screen_parser.models import ScreenData
from compass.constants import TEMPLATE_DATABASE_PATH

logger = logging.getLogger(__name__)

class TrainingAgent:
    def __init__(self):
        """Initialize training agent with YOLO detector"""
        self.detector = YOLOIconDetector()
        self.database_path = Path(__file__).parent.parent / TEMPLATE_DATABASE_PATH
        self._ensure_database_exists()
        
    def _ensure_database_exists(self):
        """Create database file if it doesn't exist"""
        if not self.database_path.exists():
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(columns=['base64_image', 'caption']).to_csv(
                self.database_path, index=False
            )
            logger.info(f"Created new template database at {self.database_path}")
    
    def process_screenshot(self, image_data: str) -> Dict:
        """
        Process screenshot using YOLO detector
        
        Args:
            image_data: Base64 encoded image
            
        Returns:
            Dict containing detected regions
        """
        # Create ScreenData object from base64 image
        screen_data = ScreenData(image_data=image_data)
        
        # Run YOLO detection
        result = self.detector.detect(screen_data)
        
        # Convert results to format expected by frontend
        detections = []
        for icon in result.icon_elements:
            detections.append({
                'bbox': icon.bbox,
                'confidence': icon.confidence
            })
            
        return {
            'detections': detections,
            'image': image_data
        }
    
    def _crop_and_encode_image(self, image_data: str, bbox: List[float]) -> str:
        """
        Crop image to bbox region and return base64 encoded result
        
        Args:
            image_data: Base64 encoded full image
            bbox: Bounding box coordinates [x1, y1, x2, y2]
            
        Returns:
            Base64 encoded cropped image
        """
        # Decode base64 image
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert bbox coordinates to integers
        x1, y1, x2, y2 = map(int, bbox)
        
        # Crop image
        cropped = img[y1:y2, x1:x2]
        
        # Encode cropped image to base64
        _, buffer = cv2.imencode('.png', cropped)
        cropped_b64 = base64.b64encode(buffer).decode('utf-8')
        
        return cropped_b64

    def save_template(self, image_data: str, caption: str, 
                     bbox: List[float]) -> None:
        """
        Save template to database
        
        Args:
            image_data: Base64 encoded image
            caption: Template caption/description
            bbox: Bounding box coordinates [x1, y1, x2, y2]
        """
        try:
            # Crop and encode the icon region
            cropped_image = self._crop_and_encode_image(image_data, bbox)
            
            # Load existing database
            df = pd.read_csv(self.database_path)
            
            # Add new template with cropped image
            new_row = pd.DataFrame([{
                'base64_image': cropped_image,
                'caption': caption
            }])
            
            # Append to database
            df = pd.concat([df, new_row], ignore_index=True)
            
            # Save updated database
            df.to_csv(self.database_path, index=False)
            logger.info(f"Saved new template with caption: {caption}")
            
        except Exception as e:
            logger.error(f"Failed to save template: {e}")
            raise

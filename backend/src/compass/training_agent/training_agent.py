import logging
import base64
from typing import Dict, List
import numpy as np
import cv2
from compass.tools.screen_parser.detectors.icon.yolo_detector import YOLOIconDetector
from compass.tools.screen_parser.models import ScreenData
from compass.database.models import Session, Template

logger = logging.getLogger(__name__)

class TrainingAgent:
    def __init__(self):
        """Initialize training agent with YOLO detector"""
        self.detector = YOLOIconDetector()
        
    def process_screenshot(self, image_data: str) -> Dict:
        """
        Process screenshot using YOLO detector
        
        Args:
            image_data: Base64 encoded image
            
        Returns:
            Dict containing detected regions
        """
        screen_data = ScreenData(image_data=image_data)
        result = self.detector.detect(screen_data)
        
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
                     bbox: List[float], agent_name: str = "OpenFoam", 
                     page_name: str = "default") -> None:
        """
        Save template to database
        
        Args:
            image_data: Base64 encoded image
            caption: Template caption/description
            bbox: Bounding box coordinates [x1, y1, x2, y2]
            agent_name: Name of the agent this template belongs to
            page_name: Name of the page this template belongs to
        """
        try:
            # Crop and encode the icon region
            cropped_image = self._crop_and_encode_image(image_data, bbox)
            
            # Create new template record
            template = Template(
                base64_image=cropped_image,
                caption=caption,
                agent_name=agent_name,
                page_name=page_name
            )
            
            # Save to database
            with Session() as session:
                session.add(template)
                session.commit()
                
            logger.info(f"Saved new template with caption: {caption}")
            
        except Exception as e:
            logger.error(f"Failed to save template: {e}")
            raise

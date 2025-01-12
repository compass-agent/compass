import logging
import base64
from typing import Dict, List
import numpy as np
import cv2
from compass.tools.screen_parser.detectors.icon.yolo_detector import YOLOIconDetector
from compass.tools.screen_parser.detectors.template_matcher.template_detector import TemplateDetector
from compass.tools.screen_parser.models import ScreenData, BoundingBox
from compass.tools.screen_parser.utils.box_utils import calculate_iou
from compass.database.models import Session, Template

logger = logging.getLogger(__name__)

IOU_THRESHOLD = 0.9  # Using same threshold as box_utils

class TrainingAgent:
    def __init__(self):
        """Initialize training agent with YOLO and template detectors"""
        self.yolo_detector = YOLOIconDetector()
        
    def process_screenshot(self, image_data: str, agent_name: str) -> Dict:
        """
        Process screenshot using template matching and YOLO detection
        
        Args:
            image_data: Base64 encoded image
            agent_name: Name of agent to filter templates
            
        Returns:
            Dict containing detected regions with labels where available
        """
        # Create ScreenData object
        screen_data = ScreenData(image_data=image_data)
        
        # First run template matching
        template_detector = TemplateDetector(agent_name=agent_name)
        template_results = template_detector.detect(screen_data)
        
        # Then run YOLO detection
        yolo_results = self.yolo_detector.detect(screen_data)
        
        # Combine results, removing YOLO detections that overlap with templates
        detections = []
        
        # Add template matches first
        for template in template_results.icon_elements:
            detections.append({
                'bbox': template.bbox,
                'confidence': template.confidence,
                'caption': template.caption  # Include template caption
            })
        
        # Add non-overlapping YOLO detections
        for yolo_detection in yolo_results.icon_elements:
            should_add = True
            
            # Create BoundingBox objects for IOU calculation
            yolo_box = BoundingBox(
                bbox=yolo_detection.bbox,
                element_type="icon",
                confidence=yolo_detection.confidence
            )
            
            # Check for overlap with template detections
            for template in template_results.icon_elements:
                template_box = BoundingBox(
                    bbox=template.bbox,
                    element_type="icon",
                    confidence=template.confidence,
                    caption=template.caption
                )
                
                if calculate_iou(yolo_box, template_box) > IOU_THRESHOLD:
                    should_add = False
                    break
            
            if should_add:
                detections.append({
                    'bbox': yolo_detection.bbox,
                    'confidence': yolo_detection.confidence,
                    'caption': None  # No caption for new YOLO detections
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
                     bbox: List[float], agent_name: str = "FreeCAD", 
                     page_name: str = "default") -> None:
        """
        Save template to database, updating caption if template already exists
        
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
            
            with Session() as session:
                # Check if template already exists
                existing_template = session.query(Template).filter_by(
                    base64_image=cropped_image,
                    agent_name=agent_name
                ).first()
                
                if existing_template:
                    # Update caption if template exists
                    existing_template.caption = caption
                    existing_template.page_name = page_name
                    logger.info(f"Updated existing template caption to: {caption}")
                else:
                    # Create new template if it doesn't exist
                    template = Template(
                        base64_image=cropped_image,
                        caption=caption,
                        agent_name=agent_name,
                        page_name=page_name
                    )
                    session.add(template)
                    logger.info(f"Saved new template with caption: {caption}")
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Failed to save template: {e}")
            raise

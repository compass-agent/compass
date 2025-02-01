import logging
import base64
from typing import Dict, List, Protocol
import numpy as np
import cv2
from compass.tools.screen_parser.detectors.icon.yolo_detector import YOLOIconDetector
from compass.tools.screen_parser.detectors.template_matcher.template_detector import TemplateDetector
from compass.tools.screen_parser.models import ScreenData, BoundingBox
from compass.tools.screen_parser.utils.box_utils import calculate_iou
from compass.database.models import Session, Template
from dataclasses import dataclass
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

logger = logging.getLogger(__name__)

IOU_THRESHOLD = 0.9  # Using same threshold as box_utils

Base = declarative_base()

@dataclass
class Detection:
    """Represents a single detection with its properties"""
    bbox: List[float]
    confidence: float
    caption: str | None
    source: str  # e.g., 'template', 'yolo'

class DetectionFilter(Protocol):
    """Protocol for detection filters"""
    def filter(self, detection: Detection, context: Dict) -> bool:
        """Return True if detection should be kept"""
        pass

class EmptyImageFilter(DetectionFilter):
    def filter(self, detection: Detection, context: Dict) -> bool:
        threshold = 10.0  # Can be made configurable
        image_data = context['image_data']
        return not self._is_empty_image(image_data, detection.bbox, threshold)
        
    def _is_empty_image(self, image_data: str, bbox: List[float], threshold: float) -> bool:
        """
        Check if cropped image region is empty (uniform color/low variation)
        
        Args:
            image_data: Base64 encoded image
            bbox: Bounding box coordinates [x1, y1, x2, y2]
            threshold: Threshold for std deviation (default 10.0)
                      Lower values = more strict (catches more uniform regions)
            
        Returns:
            bool: True if image is considered empty/uniform
        """
        # Decode and crop image
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        x1, y1, x2, y2 = map(int, bbox)
        cropped = img[y1:y2, x1:x2]
        
        # Convert to grayscale
        gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        
        # Calculate standard deviation of pixel values
        std_dev = np.std(gray)
        
        return std_dev < threshold

class SmallBoxFilter(DetectionFilter):
    def filter(self, detection: Detection, context: Dict) -> bool:
        if detection.source == 'template':  # Skip filter for templates
            return True
        return self._get_box_area(detection.bbox) >= context['min_area_threshold']
        
    def _get_box_area(self, bbox: List[float]) -> float:
        """Calculate area of bounding box"""
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width * height

class OverlapFilter(DetectionFilter):
    def filter(self, detection: Detection, context: Dict) -> bool:
        if detection.source == 'template':  # Skip filter for templates
            return True
            
        template_detections = context['template_detections']
        for template_detection in template_detections:
            # Create BoundingBox objects for IOU calculation
            box1 = BoundingBox(bbox=tuple(detection.bbox), element_type="icon", confidence=detection.confidence)
            box2 = BoundingBox(bbox=tuple(template_detection.bbox), element_type="icon", confidence=template_detection.confidence)
            
            if calculate_iou(box1, box2) > context['iou_threshold']:
                return False
        return True

class Page(Base):
    """Model for storing pages"""
    __tablename__ = 'pages'
    
    id = Column(Integer, primary_key=True)
    agent_name = Column(String, nullable=False)
    name = Column(String)  # Page name
    base64_image = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TrainingAgent:
    def __init__(self):
        """Initialize training agent with detectors and filters"""
        self.yolo_detector = YOLOIconDetector()
        self.template_detector = TemplateDetector()
        
        self.filters = [
            EmptyImageFilter(),
            SmallBoxFilter(),
            OverlapFilter()
        ]
        
    def get_screenshots(self, agent_name: str) -> List[Dict]:
        """Get all pages for an agent"""
        try:
            with Session() as session:
                pages = session.query(Page).filter_by(
                    agent_name=agent_name
                ).order_by(Page.created_at.desc()).all()
                
                return [{
                    'id': p.id,
                    'image': p.base64_image,
                    'name': p.name,  # Include page name
                    'created_at': p.created_at.isoformat()
                } for p in pages]
        except Exception as e:
            logger.error(f"Failed to get pages: {e}")
            raise

    def save_page(self, image_data: str, agent_name: str, page_name: str = "", session=None) -> tuple[int, Page]:
        """
        Save page to database if it doesn't exist
        
        Args:
            image_data: Base64 encoded image
            agent_name: Name of the agent
            page_name: Name of the page
            session: Optional SQLAlchemy session for transaction management
            
        Returns:
            tuple: (page_id, page_object)
        """
        try:
            should_close_session = session is None
            session = session or Session()
            
            # Check if page already exists
            existing = session.query(Page).filter_by(
                base64_image=image_data,
                agent_name=agent_name
            ).first()
            
            if existing:
                if page_name and existing.name != page_name:
                    existing.name = page_name
                    existing.updated_at = datetime.utcnow()
                    session.commit()
                return existing.id, existing
            
            # Create new page
            page = Page(
                base64_image=image_data,
                agent_name=agent_name,
                name=page_name
            )
            session.add(page)
            session.commit()
            return page.id, page
                
        except Exception as e:
            logger.error(f"Failed to save page: {e}")
            if should_close_session:
                session.rollback()
            raise
        finally:
            if should_close_session:
                session.close()

    def save_template(self, image_data: str, caption: str, 
                     bbox: List[float], agent_name: str = "FreeCAD", page_name: str = "") -> None:
        """Save template to database, ensuring screenshot exists first"""
        session = Session()
        try:
            # First save the full screenshot within the same session
            _, page = self.save_page(image_data, agent_name, page_name, session=session)
            
            # Then save the template
            cropped_image = self._crop_and_encode_image(image_data, bbox)
            
            existing_template = session.query(Template).filter_by(
                base64_image=cropped_image,
                agent_name=agent_name
            ).first()
            
            if existing_template:
                existing_template.caption = caption
                existing_template.page_name = page_name
                logger.info(f"Updated existing template caption to: {caption}")
            else:
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
            session.rollback()
            raise
        finally:
            session.close()

    def _calculate_size_context(self, template_detections: List[Detection], 
                              yolo_detections: List[Detection]) -> float:
        """Calculate median area and minimum threshold"""
        all_boxes = [d.bbox for d in template_detections + yolo_detections]
        if not all_boxes:
            return 0
            
        box_areas = [SmallBoxFilter()._get_box_area(bbox) for bbox in all_boxes]
        median_area = np.median(box_areas)
        return median_area * 0.2  # 20% of median area

    def process_screenshot(self, image_data: str, agent_name: str) -> Dict:
        """Process screenshot using detection pipeline"""
        # Run detectors
        screen_data = ScreenData(image_data=image_data)
        template_results = self.template_detector.detect(screen_data)
        yolo_results = self.yolo_detector.detect(screen_data)
        
        # Convert to Detection objects
        template_detections = [
            Detection(
                bbox=t.bbox,
                confidence=t.confidence,
                caption=t.caption,
                source='template'
            ) for t in template_results.icon_elements
        ]
        
        yolo_detections = [
            Detection(
                bbox=y.bbox,
                confidence=y.confidence,
                caption=None,
                source='yolo'
            ) for y in yolo_results.icon_elements
        ]
        
        # Create filter context
        context = {
            'image_data': image_data,
            'template_detections': template_detections,
            'min_area_threshold': self._calculate_size_context(
                template_detections, yolo_detections
            ),
            'iou_threshold': 0.3
        }
        
        # Apply filters to YOLO detections
        filtered_yolo = []
        for detection in yolo_detections:
            if all(f.filter(detection, context) for f in self.filters):
                filtered_yolo.append(detection)
        
        # Combine results
        all_detections = template_detections + filtered_yolo
        
        # Convert back to dictionary format
        return {
            'detections': [
                {
                    'bbox': d.bbox,
                    'confidence': d.confidence,
                    'caption': d.caption
                } for d in all_detections
            ],
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

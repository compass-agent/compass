import cv2
import numpy as np
import base64
from typing import List, Tuple, Optional
import io
from PIL import Image
import logging
from compass.tools.screen_parser.models import ScreenData
from pathlib import Path
import yaml
from compass.database.models import Session, Template

logger = logging.getLogger(__name__)

def helper_func_to_save(result: ScreenData):
    # Convert base64 image back to cv2 format
    img_bytes = base64.b64decode(result.image_data)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Draw rectangles for each detected icon
    for icon in result.icon_elements:
        x1, y1, x2, y2 = map(int, icon.bbox)  # Convert float coords to int
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Draw green rectangle
        # Optionally add caption
        cv2.putText(img, icon.caption, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2) # type: ignore

    # Save the image
    cv2.imwrite('debug_output.png', img)

class TemplateDetector:
    @staticmethod
    def load_config() -> dict:
        """Load template matching configuration from config file"""
        config_path = Path(__file__).parent.parent.parent / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('template_matching', {})

    def __init__(self, agent_name: Optional[str] = None):
        """
        Initialize template detector with configuration from config file
        
        Args:
            agent_name: Optional agent name to filter templates. If None, uses AGENT_NAME from constants
        """
        config = self.load_config()
        
        if not config.get('enabled', False):
            raise RuntimeError("Template matching is not enabled in config")
            
        self.threshold = config.get('threshold', 0.8)
        self.agent_name = agent_name if agent_name is not None else "FreeCAD"
        self.templates = self._load_templates()
        logger.info(f"Loaded {len(self.templates)} templates for agent '{self.agent_name}'")
        
    def _load_templates(self) -> List[Tuple[np.ndarray, str, str]]:
        """Load templates from database for specific agent"""
        templates = []
        
        with Session() as session:
            # Filter templates by agent_name
            db_templates = session.query(Template).filter(Template.agent_name == self.agent_name).all()
            
            for template in db_templates:
                try:
                    # Convert base64 to numpy array
                    img_bytes = base64.b64decode(template.base64_image)
                    img = Image.open(io.BytesIO(img_bytes))
                    img_array = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                    templates.append((img_array, template.caption, template.id))
                except Exception as e:
                    logger.warning(f"Failed to load template: {e}")
                    continue
                    
        return templates
    
    def detect(self, screen_data: ScreenData, agent_name: Optional[str] = None) -> ScreenData:
        """
        Detect icons in screen using template matching
        
        Args:
            screen_data: ScreenData object containing the screenshot
            agent_name: Optional agent name to filter templates. If None, uses instance agent_name
            
        Returns:
            ScreenData object with detected icons
        """
        # Use provided agent_name if given, otherwise fall back to instance agent_name
        agent_name = agent_name if agent_name is not None else self.agent_name
        
        img_bytes = base64.b64decode(screen_data.image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        screen_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        result = ScreenData(image_data=screen_data.image_data)
        
        def apply_nms(boxes, scores, template_ids, iou_threshold=0.5):
            """Apply Non-Maximum Suppression"""
            boxes = np.array(boxes)
            scores = np.array(scores)
            
            indices = np.argsort(scores)[::-1]
            keep = []
            
            while len(indices) > 0:
                keep.append(indices[0])
                
                if len(indices) == 1:
                    break
                    
                current_box = boxes[indices[0]]
                other_boxes = boxes[indices[1:]]
                
                x1 = np.maximum(current_box[0], other_boxes[:, 0])
                y1 = np.maximum(current_box[1], other_boxes[:, 1])
                x2 = np.minimum(current_box[2], other_boxes[:, 2])
                y2 = np.minimum(current_box[3], other_boxes[:, 3])
                
                w = np.maximum(0, x2 - x1)
                h = np.maximum(0, y2 - y1)
                intersection = w * h
                
                current_area = (current_box[2] - current_box[0]) * (current_box[3] - current_box[1])
                other_areas = (other_boxes[:, 2] - other_boxes[:, 0]) * (other_boxes[:, 3] - other_boxes[:, 1])
                union = current_area + other_areas - intersection
                
                iou = intersection / union
                
                indices = indices[1:][iou < iou_threshold]
                
            return keep, [template_ids[i] for i in keep]

        for template, caption, template_id in self.templates:
            try:
                h, w = template.shape[:2]
                screen_h, screen_w = screen_bgr.shape[:2]
                
                if h > screen_h or w > screen_w:
                    logger.warning(f"Template '{caption}' ({w}x{h}) is larger than image ({screen_w}x{screen_h}), skipping")
                    continue
                
                res = cv2.matchTemplate(screen_bgr, template, cv2.TM_CCOEFF_NORMED)
                
                boxes = []
                scores = []
                template_ids = []
                locations = np.where(res >= self.threshold)
                
                for pt in zip(*locations[::-1]):
                    x1, y1 = pt
                    x2, y2 = x1 + w, y1 + h
                    boxes.append([x1, y1, x2, y2])
                    scores.append(float(res[y1, x1]))
                    template_ids.append(template_id)
                
                if boxes:
                    keep_indices, kept_template_ids = apply_nms(boxes, scores, template_ids)
                    for idx, template_id in zip(keep_indices, kept_template_ids):
                        x1, y1, x2, y2 = boxes[idx]
                        result.add_icon_element(
                            bbox=(float(x1), float(y1), float(x2), float(y2)),
                            confidence=scores[idx],
                            caption=caption,
                            template_id=template_id
                        )
                    
            except Exception as e:
                logger.warning(f"Failed to process template '{caption}': {e}")
                continue
        
        logger.info(f"Found {len(result.icon_elements)} icon matches")
        return result

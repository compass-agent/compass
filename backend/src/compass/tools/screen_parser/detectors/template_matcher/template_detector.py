import cv2
import numpy as np
import pandas as pd
import base64
from typing import List, Tuple
import io
from PIL import Image
import logging
from compass.tools.screen_parser.models import ScreenData
from pathlib import Path
import yaml
from compass.constants import TEMPLATE_DATABASE_PATH
import time
from compass.database.models import Session, Template

logger = logging.getLogger(__name__)

class TemplateDetector:
    @staticmethod
    def load_config() -> dict:
        """Load template matching configuration from config file"""
        config_path = Path(__file__).parent.parent.parent / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Override database path from constants
        template_config = config.get('template_matching', {})
        template_config['database_path'] = str(Path(__file__).parent.parent.parent.parent.parent / TEMPLATE_DATABASE_PATH)
        
        return template_config

    def __init__(self):
        """Initialize template detector with configuration from config file"""
        config = self.load_config()
        
        if not config.get('enabled', False):
            raise RuntimeError("Template matching is not enabled in config")
            
        self.threshold = config.get('threshold', 0.8)
        self.templates = self._load_templates()
        logger.info(f"Loaded {len(self.templates)} templates from database")
        
    def _load_templates(self) -> List[Tuple[np.ndarray, str]]:
        """Load templates from database"""
        templates = []
        
        with Session() as session:
            db_templates = session.query(Template).all()
            
            for template in db_templates:
                try:
                    # Convert base64 to numpy array
                    img_bytes = base64.b64decode(template.base64_image)
                    img = Image.open(io.BytesIO(img_bytes))
                    img_array = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                    templates.append((img_array, template.caption))
                except Exception as e:
                    logger.warning(f"Failed to load template: {e}")
                    continue
                    
        return templates
    
    def detect(self, screen_data: ScreenData) -> ScreenData:
        """
        Detect icons in screen using template matching
        
        Args:
            screen_data: ScreenData object containing the screenshot
            
        Returns:
            ScreenData object with detected icons
        """
        # ----------
        # TODO FIXME IMPORTANT: Try SIFT  as well as template matching given that the icons may be scaled
        # ----------
        
        img_bytes = base64.b64decode(screen_data.image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        screen_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  # This reads in BGR format
        result = ScreenData(image_data=screen_data.image_data)
        
        for template, caption in self.templates:
            try:
                # Get template dimensions
                h, w = template.shape[:2]
                screen_h, screen_w = screen_bgr.shape[:2]
                
                # Skip if template is larger than image
                if h > screen_h or w > screen_w:
                    logger.warning(f"Template '{caption}' ({w}x{h}) is larger than image ({screen_w}x{screen_h}), skipping")
                    continue
                
                # Apply template matching
                res = cv2.matchTemplate(screen_bgr, template, cv2.TM_CCOEFF_NORMED)
                
                # Find locations above threshold
                locations = np.where(res >= self.threshold)
                
                for pt in zip(*locations[::-1]):  # Switch columns and rows
                    x1, y1 = pt
                    x2, y2 = x1 + w, y1 + h
                    
                    # Add detected icon to results
                    result.add_icon_element(
                        bbox=(float(x1), float(y1), float(x2), float(y2)),
                        confidence=float(res[y1, x1]),  # Use matching score as confidence
                        caption=caption
                    )
                    
            except Exception as e:
                logger.warning(f"Failed to process template '{caption}': {e}")
                continue
        
        logger.info(f"Found {len(result.icon_elements)} icon matches")
        return result

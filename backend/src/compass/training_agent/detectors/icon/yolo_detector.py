from ultralytics import YOLO
import torch
from .base import BaseIconDetector
from compass.tools.screen_parser.models import ScreenData
from pathlib import Path
import yaml
import logging
import time

class YOLOIconDetector(BaseIconDetector):
    def __init__(self):
        """Initialize YOLO detector"""
        # Set up logging
        self.logger = logging.getLogger("yolo_detector")
        self.logger.setLevel(logging.INFO)
        
        # Load config to get device setting
        config_path = Path(__file__).parent.parent.parent.parent / 'tools' / 'screen_parser' / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        self.model_path = config['icon_detection']['yolo']['model_path']
        self.conf_threshold = config['icon_detection']['yolo']['conf_threshold']
        self.iou_threshold = config['icon_detection']['yolo']['iou_threshold']
        #self.device = config['general']['device']
        # Set device based on availability
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif torch.backends.mps.is_available() and torch.backends.mps.is_built():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")
        self.model = YOLO(self.model_path)
        self.model.to(self.device)
        self.logger.info(f'YOLO model initialized on {self.device}')
    
    def detect(self, screen_data: ScreenData) -> ScreenData:
        """
        Detect icons using YOLO and return new ScreenData instance
        """
        detect_start = time.time()
        
        # Create new ScreenData instance for results
        result_screen = ScreenData(image_data=screen_data.image_data)
        
        # Use config values loaded during initialization
        kwargs = {
            'conf': self.conf_threshold,
            'iou': self.iou_threshold
        }
            
        # Run detection
        model_start = time.time()
        results = self.model(screen_data.to_pil(), **kwargs)
        model_time = time.time() - model_start
        self.logger.info(f"YOLO model inference took {model_time:.2f} seconds")
        
        # Process results
        process_start = time.time()
        if len(results) > 0:
            result = results[0]  # Get first image results
            for box, conf in zip(result.boxes.xyxy, result.boxes.conf):
                if isinstance(box, torch.Tensor):
                    box = box.cpu().numpy()
                result_screen.add_icon_element(
                    bbox=(float(box[0]), float(box[1]), float(box[2]), float(box[3])),
                    confidence=float(conf)
                )
        process_time = time.time() - process_start
        self.logger.info(f"Results processing took {process_time:.2f} seconds")
        
        total_time = time.time() - detect_start
        self.logger.info(f"Total detection time: {total_time:.2f} seconds")
        
        return result_screen 
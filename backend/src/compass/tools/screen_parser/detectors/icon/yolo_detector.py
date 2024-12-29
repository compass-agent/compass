from ultralytics import YOLO
import torch
from .base import BaseIconDetector
from .models import IconDetectionInput, IconDetectionOutput, IconBox
from pathlib import Path
import yaml
import logging
import time

class YOLOIconDetector(BaseIconDetector):
    def __init__(self):
        """
        Initialize YOLO detector
        """
        # Set up logging
        self.logger = logging.getLogger("yolo_detector")
        self.logger.setLevel(logging.INFO)
        
        # Load config to get device setting
        config_path = Path(__file__).parent.parent.parent / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        self.model_path = config['icon_detection']['yolo']['model_path']
        self.conf_threshold = config['icon_detection']['yolo']['conf_threshold']
        self.iou_threshold = config['icon_detection']['yolo']['iou_threshold']
        self.device = config['general']['device']
        self.model = YOLO(self.model_path)
        self.model.to(self.device)
        self.logger.info(f'YOLO model initialized on {self.device}')
    
    def detect(self, input_data: IconDetectionInput) -> IconDetectionOutput:
        """
        Detect icons using YOLO
        """
        detect_start = time.time()
        
        # Use config values loaded during initialization
        kwargs = {
            'conf': self.conf_threshold,
            'iou': self.iou_threshold
        }
        if input_data.image_size:
            kwargs['imgsz'] = input_data.image_size[0]
            
        # Run detection
        model_start = time.time()
        results = self.model(input_data.to_pil(), **kwargs) # type: ignore
        model_time = time.time() - model_start
        self.logger.info(f"YOLO model inference took {model_time:.2f} seconds")
        
        # Process results
        process_start = time.time()
        boxes = []
        if len(results) > 0:
            result = results[0]  # Get first image results
            for box, conf in zip(result.boxes.xyxy, result.boxes.conf):
                if isinstance(box, torch.Tensor):
                    box = box.cpu().numpy()
                boxes.append(IconBox(
                    bbox=tuple(float(x) for x in box), # type: ignore
                    confidence=float(conf)
                ))
        process_time = time.time() - process_start
        self.logger.info(f"Results processing took {process_time:.2f} seconds")
        
        total_time = time.time() - detect_start
        self.logger.info(f"Total detection time: {total_time:.2f} seconds")
        
        return IconDetectionOutput(boxes=boxes) 
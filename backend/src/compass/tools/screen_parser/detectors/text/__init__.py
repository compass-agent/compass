from .base import BaseTextDetector
from .paddle_detector import PaddleTextDetector
from .easyocr_detector import EasyOCRDetector
from .google_detector import GoogleCloudTextDetector
from .factory import TextDetectorFactory

__all__ = [
    'BaseTextDetector',
    'PaddleTextDetector',
    'EasyOCRDetector',
    'GoogleCloudTextDetector',
    'TextDetectorFactory'
]

import pandas as pd
from pathlib import Path
import yaml
import logging
import time

from compass.tools.screen_parser.utils.box_utils import remove_overlapping_boxes
from compass.tools.screen_parser.utils.visualization import visualize_boxes
from compass.tools.screen_parser.detectors.icon.factory import IconDetectorFactory
from compass.tools.screen_parser.detectors.text.factory import TextDetectorFactory
from compass.tools.screen_parser.captioners.factory import CaptionerFactory
from compass.tools.screen_parser.models import ScreenData
from compass.tools.screen_parser.detectors.template_matcher.template_detector import TemplateDetector

logger = logging.getLogger(__name__)

class ScreenParser:
    def __init__(self):
        """
        Initialize ScreenParser with settings from config file
        """        
        # Set up logging with more explicit configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - [SCREEN PARSER] - %(message)s',
            force=True  # Force override any existing logger
        )
        logger.setLevel(logging.INFO)  # Explicitly set level
        
        # Test that logging is working
        logger.info("ScreenParser initialized")
        
        # Load config
        config_path = Path(__file__).parent / 'config.yaml'
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Get settings from config
        self.caption_enabled = self.config['captioning']['enabled']
        self.include_text_in_description = self.config['general']['screen_descriptor']['include_text']
        
        # Initialize detectors using factories
        #self.icon_detector = IconDetectorFactory.create_detector()
        #self.text_detector = TextDetectorFactory.create_detector()
        
        # Initialize template matcher separately
        self.template_matcher = TemplateDetector()

        #if self.caption_enabled:
        #    self.captioner = CaptionerFactory.create_captioner()
        #else:
        #    self.captioner = None

    def parse(self, screen_data: ScreenData) -> ScreenData:
        """Parse a screen and identify all elements"""
        parse_start = time.time()
        
        icon_start = time.time()
        icon_results = self.icon_detector.detect(screen_data)
        logger.info(f"Icon detection took {time.time() - icon_start:.2f} seconds")
        
        text_start = time.time()
        text_results = self.text_detector.detect(screen_data)
        logger.info(f"Text detection took {time.time() - text_start:.2f} seconds")
        
        merged_screen_data = remove_overlapping_boxes(icon_results, text_results)
        
        if self.captioner:
            caption_start = time.time()
            merged_screen_data = self.captioner.generate_captions(merged_screen_data)
            logger.info(f"Captioning took {time.time() - caption_start:.2f} seconds")
        
        # Generate and add screen description
        description = self.screen_descriptor(merged_screen_data)
        merged_screen_data.description = description
        
        logger.info(f"Total parsing took {time.time() - parse_start:.2f} seconds")
        return merged_screen_data

    def light_parse(self, screen_data: ScreenData) -> ScreenData:
        """
        Lightweight parsing using only template matching and screen description.
        Faster alternative to full parse() method.
        """
        parse_start = time.time()
        
        # Only run template matching for icon detection
        detection_start = time.time()
        detected_screen = self.template_matcher.detect(screen_data)
        logger.info(f"Template matching detection took {time.time() - detection_start:.2f} seconds")
        
        # Generate and add screen description
        description = self.screen_descriptor(detected_screen)
        detected_screen.description = description
        
        logger.info(f"Total light parsing took {time.time() - parse_start:.2f} seconds")
        return detected_screen

    def screen_descriptor(self, screen_data: ScreenData) -> str:
        """
        Create a structured description of elements in the screen
        
        Args:
            screen_data (ScreenData): Detection results in ScreenData format
            
        Returns:
            str: Formatted screen description
        """
        # Convert ScreenData elements to DataFrame for processing
        # check if no elements are present or if elements are empty
        if not screen_data.elements or all(not element.coordinates for element in screen_data.elements):
            return ""
        
        elements_data = []
        for element in screen_data.elements:
            coords = element.coordinates
            elements_data.append({
                'type': element.element_type,
                'text': element.text or element.caption,
                'x1': coords['x1'],
                'y1': coords['y1'],
                'x2': coords['x2'],
                'y2': coords['y2']
            })
        df = pd.DataFrame(elements_data)
        
        # Create copy of relevant elements
        if self.include_text_in_description:
            elements_df = df.copy()
        else:
            elements_df = df[df['type'] == 'icon'].copy()
        
        # Calculate center coordinates
        elements_df['center_x'] = (elements_df['x1'] + elements_df['x2']) / 2
        elements_df['center_y'] = (elements_df['y1'] + elements_df['y2']) / 2
        
        # Sort by y first (top to bottom), then x (left to right)
        elements_df = elements_df.sort_values(['center_y', 'center_x'])
        
        if self.include_text_in_description:
            des = "Below is a list of elements (icons and text) detected on the screen, sorted from top-left to bottom-right. " \
                  "There might be some icons not being matched or labeled. While the descriptions may have slight inaccuracies, " \
                  "the coordinate positions are reliable. When referencing these elements, please use the provided coordinates as their exact locations, if possible."
        else:
            des = "Below is a list of icons detected on the screen, sorted from top-left to bottom-right. " \
                  "There are some unnamed icons. While the descriptions may have slight inaccuracies, " \
                  "the coordinate positions are reliable. When referencing these icons, please use the provided coordinates as their exact locations."
        
        descriptions = [des]
        
        for _, element in elements_df.iterrows():
            if element['type'] == 'icon':
                icon_text = "unnamed icon" if pd.isna(element['text']) else element['text']
                desc = f"Icon: {icon_text} [{int(element['center_x'])}, {int(element['center_y'])}]"
            else:  # text element
                desc = f"Text element: {element['text']} [{int(element['center_x'])}, {int(element['center_y'])}]"
            descriptions.append(desc)
        
        screen_desc = "\n".join(descriptions)
        
        return screen_desc

if __name__ == "__main__":
    # Import and set API keys
    import sys
    from pathlib import Path
    import os
    
    # Add SingleTest directory to Python path to import key
    project_root = Path(__file__).parent.parent
    sys.path.append(str(project_root))
    # Set up paths
    base_path = Path(__file__).parent
    test_image = base_path / 'imgs/last_image.png'
    
    try:
        # Initialize parser
        parser = ScreenParser()
        print("Initialized parser with both full and light parsing capabilities")
        
        # Create ScreenData from image file
        screen_data = ScreenData.from_path(str(test_image))
        
        # Test both parsing methods
        print("\nTesting light parse...")
        light_parsed = parser.light_parse(screen_data)
        print(f"Light parse description:\n{light_parsed.description}\n")
        
        print("\nTesting full parse...")
        full_parsed = parser.parse(screen_data)
        print(f"Full parse description:\n{full_parsed.description}\n")
        
        # Save results
        base_name = test_image.stem
        
        # Save light parse results
        light_desc_path = test_image.with_suffix('.light.desc.txt')
        with open(light_desc_path, 'w') as f:
            f.write(light_parsed.description or "")
        
        light_output_path = base_path / f'imgs/{base_name}_light_annotated.png'
        visualize_boxes(str(test_image), light_parsed, str(light_output_path))
        
        # Save full parse results
        full_desc_path = test_image.with_suffix('.full.desc.txt')
        with open(full_desc_path, 'w') as f:
            f.write(full_parsed.description or "")
        
        full_output_path = base_path / f'imgs/{base_name}_full_annotated.png'
        visualize_boxes(str(test_image), full_parsed, str(full_output_path))
        
    except Exception as e:
        print(f"Error processing image: {e}") 
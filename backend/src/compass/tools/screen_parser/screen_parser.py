from enum import Enum, auto
import pandas as pd
import numpy as np
from PIL import Image
from pathlib import Path
import os
import base64
import io
import yaml
import logging
import time

from screen_parser.detectors.text import TextDetectionInput
from screen_parser.detectors.icon import IconDetectionInput
from screen_parser.captioners import CaptioningInput
from screen_parser.utils.box_utils import remove_overlapping_boxes
from screen_parser.utils.visualization import visualize_boxes
from screen_parser.detectors.icon.factory import IconDetectorFactory
from screen_parser.detectors.text.factory import TextDetectorFactory
from screen_parser.captioners.factory import CaptionerFactory

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
        self.logger = logging.getLogger("screen_parser")  # Give it a specific name
        self.logger.setLevel(logging.INFO)  # Explicitly set level
        
        # Test that logging is working
        self.logger.info("ScreenParser initialized")
        
        # Load config
        config_path = Path(__file__).parent / 'config.yaml'
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Get settings from config
        self.caption_enabled = self.config['captioning']['enabled']
        self.include_text_in_description = self.config['general']['screen_descriptor']['include_text']
        
        # Initialize detectors using factories
        self.icon_detector = IconDetectorFactory.create_detector()
        self.text_detector = TextDetectorFactory.create_detector()
        
        if self.caption_enabled:
            self.captioner = CaptionerFactory.create_captioner()
        else:
            self.captioner = None

    def parse(self, base64_image: str) -> pd.DataFrame:
        """
        Detect and analyze elements in the image
        
        Args:
            base64_image (str): Base64 encoded image string
            
        Returns:
            pd.DataFrame: Detection results
        """        
        parse_start = time.time()
        
        # Run icon detection with new API
        icon_start = time.time()
        icon_input = IconDetectionInput.from_base64(base64_image)
        icon_output = self.icon_detector.detect(icon_input)
        self.logger.info(f"Icon detection took {time.time() - icon_start:.2f} seconds")
        
        # Run text detection with new API
        text_start = time.time()
        text_input = TextDetectionInput.from_base64(base64_image)
        text_output = self.text_detector.detect(text_input)
        self.logger.info(f"Text detection took {time.time() - text_start:.2f} seconds")
        
        # Get image dimensions from base64
        image_source = np.array(Image.open(io.BytesIO(base64.b64decode(base64_image))).convert('RGB'))        
        
        # Handle overlaps with new unified interface
        filtered_boxes = remove_overlapping_boxes(icon_output, text_output)
        
        # Generate captions if enabled, otherwise use default "icon" text
        icon_boxes = [
            box.bbox for box in filtered_boxes 
            if box.box_type == 'icon'
        ]
        if icon_boxes:
            if self.captioner:
                caption_start = time.time()
                caption_input = CaptioningInput(
                    image=image_source,
                    boxes=icon_boxes,
                    batch_size=32
                )
                caption_output = self.captioner.generate_captions(caption_input)
                self.logger.info(f"Captioning took {time.time() - caption_start:.2f} seconds")
                
                caption_idx = 0
                for box in filtered_boxes:
                    if box.box_type == 'icon':
                        box.content = caption_output.captions[caption_idx]
                        caption_idx += 1
            else:
                # Add default "icon" caption when captioning is disabled
                for box in filtered_boxes:
                    if box.box_type == 'icon':
                        box.content = "icon"
        
        # Convert to DataFrame
        detections = [
            {
                'x1': round(box.bbox[0], 2),
                'y1': round(box.bbox[1], 2),
                'x2': round(box.bbox[2], 2),
                'y2': round(box.bbox[3], 2),
                'type': box.box_type,
                'text': box.content,
                'interactivity': box.interactivity
            }
            for box in filtered_boxes
        ]
        
        df = pd.DataFrame(detections)
        print(f"\nFound {len(df[df['type']=='icon'])} icons and {len(df[df['type']=='text'])} text elements")
        
        self.logger.info(f"Total parsing took {time.time() - parse_start:.2f} seconds")
        return df

    def visualize_boxes(self, image_path, boxes_df, output_path=None):
        """Wrapper for visualization utility"""
        return visualize_boxes(image_path, boxes_df, output_path)

    def save_results(self, df, output_path):
        """Save detection results to CSV"""
        df.to_csv(output_path, index=False)
        print(f"Results saved to: {output_path}") 

    def screen_descriptor(self, df):
        """
        Create a structured description of elements in the screen
        
        Args:
            df (pd.DataFrame): Detection results DataFrame
            output_path (str, optional): Path to save description text
            
        Returns:
            str: Formatted screen description
        """
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
    from SingleTest.key import ANTHROPIC_API_KEY
    os.environ['ANTHROPIC_API_KEY'] = ANTHROPIC_API_KEY

    # Set up paths
    base_path = Path(__file__).parent
    test_image = base_path / 'imgs/last_image.png'
    
    try:
        # Initialize parser
        parser = ScreenParser()
        print("Initialized with Anthropic captioning and Google Cloud Vision text detection")
        
        # Load and encode image
        with open(test_image, 'rb') as image_file:
            base64_image = base64.b64encode(image_file.read()).decode()
        
        # Detect objects and generate captions
        results_df = parser.parse(base64_image)
        
        # Save results to CSV
        csv_path = test_image.with_suffix('.csv')
        parser.save_results(results_df, str(csv_path))
        
        # Generate and save screen description
        desc_path = test_image.with_suffix('.desc.txt')
        screen_desc = parser.screen_descriptor(results_df)
        output_path = str(desc_path)
        # Save if output path provided
        if output_path:
            output_path = Path(output_path).with_suffix('.txt')
            with open(output_path, 'w') as f:
                f.write(screen_desc)
        # Generate and save visualization
        output_path = base_path / 'imgs/last_image_annotated.png'
        parser.visualize_boxes(str(test_image), results_df, str(output_path))
        
    except Exception as e:
        print(f"Error processing image: {e}") 
import pandas as pd
from pathlib import Path
import yaml
import logging
import time

from compass.tools.screen_parser.models import ScreenData
from compass.tools.screen_parser.detectors.template_matcher.conv_template_detector import ConvTemplateDetector
from compass.utils.utility import log_execution_time
logger = logging.getLogger(__name__)

class ScreenParser:
    def __init__(self, agent_name: str = "structural-engineer"):
        """
        Initialize ScreenParser with convolution-based template detector
        
        Args:
            agent_name: Name of the agent for template filtering
        """           
        logger.info("ScreenParser initialized with convolution-based template matching")
        
        # Load config
        config_path = Path(__file__).parent / 'config.yaml'
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Get settings from config
        self.include_text_in_description = self.config['general']['screen_descriptor']['include_text']
        
        # Initialize convolution-based template detector
        self.template_detector = ConvTemplateDetector(agent_name=agent_name)

    @log_execution_time(logger)
    def parse(self, screen_data: ScreenData) -> ScreenData:
        """Parse a screen using convolution-based template matching"""
        return self.light_parse(screen_data)
    
    @log_execution_time(logger)
    def light_parse(self, screen_data: ScreenData, x_scaling_factor: float = 1.0, y_scaling_factor: float = 1.0) -> ScreenData:
        """
        Fast parsing using convolution-based template matching
        
        Args:
            screen_data (ScreenData): The screen data to parse
            x_scaling_factor (float): Factor to scale x coordinates
            y_scaling_factor (float): Factor to scale y coordinates
        """
        
        # Run convolution-based template detection
        detection_start = time.time()
        detected_screen = self.template_detector.detect(screen_data)
        logger.info(f"Convolution template detection took {time.time() - detection_start:.2f} seconds")
        
        # Generate and add screen description with scaling factors
        description = self.screen_descriptor(detected_screen, x_scaling_factor, y_scaling_factor)
        detected_screen.description = description
        return detected_screen

    @log_execution_time(logger)
    def screen_descriptor(self, screen_data: ScreenData, x_scaling_factor: float = 1.0, y_scaling_factor: float = 1.0) -> str:
        """
        Create a structured description of elements in the screen
        
        Args:
            screen_data (ScreenData): Detection results in ScreenData format
            x_scaling_factor (float): Factor to scale x coordinates
            y_scaling_factor (float): Factor to scale y coordinates
            
        Returns:
            str: Formatted screen description
        """
        # Convert ScreenData elements to DataFrame for processing
        # check if no elements are present or if elements are empty
        if not screen_data.elements:
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
        
        # Calculate center coordinates and apply scaling
        elements_df['center_x'] = ((elements_df['x1'] + elements_df['x2']) / 2) * x_scaling_factor
        elements_df['center_y'] = ((elements_df['y1'] + elements_df['y2']) / 2) * y_scaling_factor
        
        # Sort by y first (top to bottom), then x (left to right)
        elements_df = elements_df.sort_values(by=['center_y', 'center_x'])
        
        if self.include_text_in_description:
            des = "Below is a list of elements (icons and text) detected on the screen, sorted from top-left to bottom-right. " \
                  "There might be some icons not being matched or labeled. While the descriptions may have slight inaccuracies, " \
                  "the coordinate positions are reliable. When referencing these elements, please use the provided coordinates as their exact locations, if possible."
        else:
            des = "\n\nBelow is a list of icons detected on the screen, sorted from top-left to bottom-right. " \
                  "There are some unnamed icons or unmatched icons. While the descriptions may have slight inaccuracies, " \
                  "the coordinate positions are reliable. When referencing these icons, please use the provided coordinates as their exact locations. \n\n"
        
        descriptions = [des]
        
        for _, element in elements_df.iterrows():
            if element['type'] == 'icon':
                text_val = element['text']
                icon_text = "unnamed icon" if text_val is None or (isinstance(text_val, float) and pd.isna(text_val)) else str(text_val)
                desc = f"Icon: {icon_text} [{int(element['center_x'])}, {int(element['center_y'])}]"
            else:  # text element
                desc = f"Text element: {element['text']} [{int(element['center_x'])}, {int(element['center_y'])}]"
            descriptions.append(desc)
        
        screen_desc = "\n".join(descriptions)
        
        return screen_desc

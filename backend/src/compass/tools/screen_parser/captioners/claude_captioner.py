from .base import BaseCaptioner
from compass.tools.screen_parser.models import ScreenData
import anthropic
from PIL import Image
import base64
from io import BytesIO
import os
from pathlib import Path
import yaml
import logging
import time
from typing import Tuple

logger = logging.getLogger(__name__)

class ClaudeModelConfig:
    SONNET = "claude-3-5-sonnet-20241022"
    HAIKU = "claude-3-5-haiku-20241022"
    
    @staticmethod
    def get_costs(model_name):
        costs = {
            ClaudeModelConfig.SONNET: {"input": 3.0 / 1_000_000, "output": 15.0 / 1_000_000},
            ClaudeModelConfig.HAIKU: {"input": 0.8 / 1_000_000, "output": 3.0 / 1_000_000}
        }
        return costs.get(model_name, costs[ClaudeModelConfig.SONNET])

class ClaudeCaptioner(BaseCaptioner):
    def __init__(self):
        # Load config
        config_path = Path(__file__).parent.parent / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Use model from config if not provided
        self.model_name = config['captioning']['claude']['model']
        self.save_debug_crops = config['captioning']['claude'].get('save_debug_crops', False)
        # Only initialize Claude client if needed

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        self.client = anthropic.Anthropic(api_key=api_key, max_retries=4)
        self.costs = ClaudeModelConfig.get_costs(self.model_name)
        
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        
        # Create a reusable message template with cached system prompt
        self.message_template = {
            "model": self.model_name,
            "max_tokens": 10,
            "system": "Identify this Mac UI element in 2-3 words. The first image shows the context area, and the second image shows the specific icon or element to identify.",
            "messages": [{
                "role": "user",
                "content": []  # Will be populated with images during generation
            }]
        }

    def _preprocess_box(self, 
            input_data, 
            box: tuple, 
            image_height: int, 
            image_width: int) -> dict:
        """Preprocess a single bounding box and return message data and debug info"""
        xmin, ymin, xmax, ymax = [int(coord) for coord in box]
        
        # Calculate context window dimensions
        box_width = xmax - xmin
        box_height = ymax - ymin
        margin_scale = 3
        context_xmin = max(0, xmin - (box_width * margin_scale))
        context_xmax = min(image_width, xmax + (box_width * margin_scale))
        context_ymin = max(0, ymin - (box_height * margin_scale))
        context_ymax = min(image_height, ymax + (box_height * margin_scale))
        
        # Crop and process images
        context_image = Image.fromarray(input_data.image[context_ymin:context_ymax, context_xmin:context_xmax])
        icon_image = Image.fromarray(input_data.image[ymin:ymax, xmin:xmax])
        
        # Reduce context image resolution
        new_size = (context_image.width // 2, context_image.height // 2)
        context_image = context_image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save debug images
        self._save_cropped_image(icon_image, context_image, (xmin, xmax, ymin, ymax))
        
        # Convert images to base64
        context_buffered = BytesIO()
        icon_buffered = BytesIO()
        context_image.save(context_buffered, format="PNG")
        icon_image.save(icon_buffered, format="PNG")
        context_str = base64.b64encode(context_buffered.getvalue()).decode()
        icon_str = base64.b64encode(icon_buffered.getvalue()).decode()
        
        # Prepare message data
        message_data = self.message_template.copy()
        message_data["messages"][0]["content"] = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": context_str,
                }
            },
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": icon_str,
                }
            }
        ]
        
        return message_data

    def _get_caption(self, message_data: dict) -> Tuple[str, dict | None]:
        """Make synchronous API call to get caption"""
        try:
            message = self.client.messages.create(**message_data)
            return message.content[0].text.strip(), message
        except Exception as e:
            logger.error(f"Error generating caption: {e}")
            return "Error: Could not generate caption", None

    def generate_captions(self, screen_data: ScreenData) -> ScreenData:
        """Generate captions for icons in the screen data"""
        if not screen_data.icon_elements:
            return screen_data
            
        start_time = time.time()
        logger.info(f"Starting caption generation for {len(screen_data.icon_elements)} icons")
        
        # Get image and dimensions
        image = screen_data.to_pil()
        image_width, image_height = image.size
        
        # Process each icon
        for icon in screen_data.icon_elements:
            try:
                message_data = self._preprocess_box(
                    screen_data, icon.bbox, image_height, image_width
                )
                caption, message = self._get_caption(message_data)
                icon.caption = caption  # Only assign the caption string
                if message:
                    self._update_usage_stats(message)
            except Exception as e:
                logger.error(f"Error preprocessing icon: {e}")

        logger.info(f"Caption generation completed in {time.time() - start_time:.2f} seconds")
        return screen_data

    def _update_usage_stats(self, message):
        """Update token usage and cost statistics"""
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        
        # Calculate cost for this message
        input_cost = input_tokens * self.costs["input"]
        output_cost = output_tokens * self.costs["output"]
        self.total_cost += input_cost + output_cost

    def get_usage_stats(self):
        """
        Get current usage statistics
        
        Returns:
            dict: Current usage statistics and costs
        """
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 6)
        }

    def _save_cropped_image(self, icon_image, context_image, coordinates):
        """
        Save both cropped icon and context images with coordinates as the filename.
        
        Args:
            icon_image (PIL.Image): The icon image to save
            context_image (PIL.Image): The context image to save
            coordinates (tuple): Tuple of (xmin, xmax, ymin, ymax)
        """
        save_dir = os.path.join(os.path.dirname(__file__), '..', 'imgs', 'caption', 'last_image')
        os.makedirs(save_dir, exist_ok=True)
        
        xmin, xmax, ymin, ymax = coordinates
        base_filename = f"{xmin}_{xmax}_{ymin}_{ymax}"
        
        # Save icon image
        icon_path = os.path.join(save_dir, f"{base_filename}_icon.png")
        icon_image.save(icon_path)
        
        # Save context image
        context_path = os.path.join(save_dir, f"{base_filename}_context.png")
        context_image.save(context_path)

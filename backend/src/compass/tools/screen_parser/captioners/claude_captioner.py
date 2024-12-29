from .base import BaseCaptioner
from .models import CaptioningInput, CaptioningOutput
import anthropic
from PIL import Image
import base64
from io import BytesIO
import os
import asyncio
from typing import List, Tuple
from pathlib import Path
import yaml
from .icon_matcher import IconMatcher, BatchMatchResult

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
        self.run_claude = config['captioning']['claude'].get('run_claude', False)
        
        # Initialize IconMatcher
        icon_matcher_config = config['captioning']['claude']['icon_matcher']
        self.icon_matcher = IconMatcher(
            similarity_threshold=icon_matcher_config['similarity_threshold']
        )
        self.icon_matcher.load_database(icon_matcher_config['database_path'])
        
        # Only initialize Claude client if needed
        if self.run_claude:
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
            image_width: int) -> Tuple[dict, tuple]:
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
        
        return message_data, (xmin, xmax, ymin, ymax)

    async def _get_caption(self, message_data: dict) -> Tuple[str, dict]:
        """Make async API call to get caption"""
        try:
            message = self.client.messages.create(**message_data)
            return message.content[0].text.strip(), message
        except Exception as e:
            print(f"Error generating caption: {e}")
            return "Error: Could not generate caption", None # type: ignore

    def generate_captions(self, input_data: CaptioningInput) -> CaptioningOutput:
        image_height, image_width = input_data.image.shape[:2]
        
        # Preprocess all boxes and collect base64 images
        base64_images = []
        for box in input_data.boxes:
            try:
                message_data, _ = self._preprocess_box(input_data, box, image_height, image_width)
                # Extract icon image base64 from message data
                icon_data = message_data["messages"][0]["content"][1]["source"]["data"]
                base64_images.append(icon_data)
            except Exception as e:
                print(f"Error preprocessing box {box}: {e}")
                base64_images.append(None)

        if self.run_claude:
            # Prepare message data for each valid image
            message_data_list = []
            for box in input_data.boxes:
                try:
                    message_data, _ = self._preprocess_box(input_data, box, image_height, image_width)
                    message_data_list.append(message_data)
                except Exception as e:
                    print(f"Error preprocessing box {box}: {e}")
                    message_data_list.append(None)

            # Create and run async tasks only for the LLM calls
            async def process_all_captions():
                tasks = [
                    self._get_caption(data)
                    for data in message_data_list
                    if data is not None
                ]
                results = await asyncio.gather(*tasks)
                return results
            
            # Run async processing for LLM calls
            results = asyncio.run(process_all_captions())
            
            # Process results
            generated_texts = []
            for caption, message in results:
                generated_texts.append(caption)
                if message:
                    self._update_usage_stats(message)
        else:
            # Use IconMatcher
            # Filter out None values
            valid_images = [img for img in base64_images if img is not None]
            
            # Get matches using IconMatcher
            results = self.icon_matcher.find_matches_batch(valid_images)
            
            # Convert results to captions list
            generated_texts = []
            result_idx = 0
            for base64_img in base64_images:
                if base64_img is None:
                    generated_texts.append(None)
                else:
                    match = results.matches[result_idx]
                    generated_texts.append(match.caption if match else None)
                    result_idx += 1
        
        return CaptioningOutput(
            captions=generated_texts,
            metadata=self.get_usage_stats()
        )

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
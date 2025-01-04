import torch
from transformers import AutoProcessor, AutoModelForCausalLM
from .base import BaseCaptioner
from compass.tools.screen_parser.models import ScreenData
import yaml
from pathlib import Path
import logging
import time

class FlorenceCaptioner(BaseCaptioner):
    def __init__(self):
        self.logger = logging.getLogger("florence_captioner")
        self.logger.setLevel(logging.INFO)
        
        config_path = Path(__file__).parent.parent / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.device = config['general']['device']
        self.model_path = config['captioning']['florence']['model_path']
        self.batch_size = config['captioning']['florence'].get('batch_size', 4)
        
        # Initialize model and processor
        self.logger.info(f"Loading Florence model from {self.model_path}")
        self.processor = AutoProcessor.from_pretrained(self.model_path, trust_remote_code=True)
        dtype = torch.float16 if self.device != 'cpu' else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path, torch_dtype=dtype, trust_remote_code=True
        )
        self.model.to(self.device)
        self.logger.info(f"Florence model loaded and moved to {self.device}")

    @torch.inference_mode()
    def generate_captions(self, screen_data: ScreenData) -> ScreenData:
        """Generate captions for icons in the screen data"""
        if not screen_data.icon_elements:
            return screen_data
            
        start_time = time.time()
        self.logger.info(f"Starting caption generation for {len(screen_data.icon_elements)} icons")
        
        # Get image crops for each icon
        image = screen_data.to_pil()
        crops = []
        for icon in screen_data.icon_elements:
            x1, y1, x2, y2 = [int(coord) for coord in icon.bbox]
            crop = image.crop((x1, y1, x2, y2))
            crops.append(crop)
        
        # Process in batches
        prompt = "<CAPTION>"
        for i in range(0, len(crops), self.batch_size):
            batch = crops[i:i+self.batch_size]
            
            # Prepare inputs
            inputs = self.processor(
                images=batch, 
                text=[prompt] * len(batch), 
                return_tensors="pt"
            ).to(device=self.device)
            
            if self.device == 'cuda':
                inputs = {k: v.to(dtype=torch.float16) for k, v in inputs.items()}
            
            # Generate captions
            generated_ids = self.model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=100,
                num_beams=3,
                do_sample=False
            )
            
            # Decode captions
            captions = self.processor.batch_decode(generated_ids, skip_special_tokens=True)
            
            # Update icons with captions
            for j, caption in enumerate(captions):
                idx = i + j
                if idx < len(screen_data.icon_elements):
                    screen_data.icon_elements[idx].caption = caption.strip()
        
        self.logger.info(f"Caption generation completed in {time.time() - start_time:.2f} seconds")
        return screen_data 
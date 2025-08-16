import torch
from transformers import Blip2Processor, Blip2ForConditionalGeneration
from torchvision.transforms import ToPILImage
from .base import BaseCaptioner
from compass.tools.screen_parser.models import ScreenData
import yaml
from pathlib import Path
import logging
import time


logger = logging.getLogger(__name__)


class BLIP2Captioner(BaseCaptioner):
    def __init__(self, model_path=None):
        logger.setLevel(logging.INFO)
        
        # Load config to get device setting and model path
        config_path = Path(__file__).parent.parent.parent / 'tools' / 'screen_parser' / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.device = config['general']['device']
        self.model_path = model_path or config['captioning']['blip2']['model_path']
        self.batch_size = config['captioning']['blip2'].get('batch_size', 4)
        
        self.to_pil = ToPILImage()
        
        # Initialize model and processor
        logger.info(f"Loading BLIP2 model from {self.model_path}")
        self.processor = Blip2Processor.from_pretrained(self.model_path)
        dtype = torch.float16 if self.device != 'cpu' else torch.float32
        self.model = Blip2ForConditionalGeneration.from_pretrained(
            self.model_path, device_map=None, torch_dtype=dtype
        )
        self.model.to(self.device) # type: ignore
        logger.info(f"BLIP2 model loaded and moved to {self.device}")

    @torch.inference_mode()
    def generate_captions(self, screen_data: ScreenData) -> ScreenData:
        """Generate captions for icons in the screen data"""
        if not screen_data.icon_elements:
            return screen_data
            
        start_time = time.time()
        logger.info(f"Starting caption generation for {len(screen_data.icon_elements)} icons")
        
        # Get image crops for each icon
        image = screen_data.to_pil()
        crops = []
        for icon in screen_data.icon_elements:
            x1, y1, x2, y2 = [int(coord) for coord in icon.bbox]
            crop = image.crop((x1, y1, x2, y2))
            crops.append(crop)
        
        # Process in batches
        prompt = "The image shows"
        for i in range(0, len(crops), self.batch_size):
            batch = crops[i:i+self.batch_size]
            
            # Prepare inputs
            inputs = self.processor(
                images=batch, 
                text=[prompt] * len(batch), 
                return_tensors="pt"
            ).to(device=self.device) # type: ignore
            
            if self.device == 'cuda':
                inputs = {k: v.to(dtype=torch.float16) for k, v in inputs.items()}
            
            # Generate captions
            generated_ids = self.model.generate(
                **inputs, # type: ignore
                max_length=100,
                num_beams=5,
                no_repeat_ngram_size=2,
                early_stopping=True,
                num_return_sequences=1
            )
            
            # Decode captions
            captions = self.processor.batch_decode(generated_ids, skip_special_tokens=True) # type: ignore
            
            # Update icons with captions
            for j, caption in enumerate(captions):
                idx = i + j
                if idx < len(screen_data.icon_elements):
                    screen_data.icon_elements[idx].caption = caption.strip()
        
        logger.info(f"Caption generation completed in {time.time() - start_time:.2f} seconds")
        return screen_data 
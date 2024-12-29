import torch
from transformers import Blip2Processor, Blip2ForConditionalGeneration
from torchvision.transforms import ToPILImage
from .base import BaseCaptioner
from .models import CaptioningInput, CaptioningOutput
import yaml
from pathlib import Path

class BLIP2Captioner(BaseCaptioner):
    def __init__(self, model_path=None):
        # Load config to get device setting and model path
        config_path = Path(__file__).parent.parent / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.device = config['general']['device']
        # Use model_path from config if not provided
        self.model_path = model_path or config['captioning']['blip2']['model_path']
        
        self.to_pil = ToPILImage()
        
        # Initialize model and processor
        self.processor = Blip2Processor.from_pretrained(self.model_path)
        dtype = torch.float16 if self.device != 'cpu' else torch.float32
        self.model = Blip2ForConditionalGeneration.from_pretrained(
            self.model_path, device_map=None, torch_dtype=dtype
        )
        self.model.to(self.device) # type: ignore

    @torch.inference_mode()
    def generate_captions(self, input_data: CaptioningInput) -> CaptioningOutput:
        crops = input_data.get_crops()
        prompt = input_data.prompt or "The image shows"
        
        generated_texts = []
        for i in range(0, len(crops), input_data.batch_size):
            batch = crops[i:i+input_data.batch_size]
            
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
            texts = self.processor.batch_decode(generated_ids, skip_special_tokens=True) # type: ignore
            generated_texts.extend(text.strip() for text in texts)
            
        return CaptioningOutput(captions=generated_texts) 
import torch
from transformers import AutoProcessor, AutoModelForCausalLM
from .base import BaseCaptioner
from .models import CaptioningInput, CaptioningOutput
import yaml
from pathlib import Path

class FlorenceCaptioner(BaseCaptioner):
    def __init__(self):
        config_path = Path(__file__).parent.parent / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self.device = config['general']['device']
        self.model_path = config['captioning']['florence']['model_path']
        
        # Initialize model and processor
        self.processor = AutoProcessor.from_pretrained(self.model_path, trust_remote_code=True)
        dtype = torch.float16 if self.device != 'cpu' else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path, torch_dtype=dtype, trust_remote_code=True
        )
        self.model.to(self.device)

    @torch.inference_mode()
    def generate_captions(self, input_data: CaptioningInput) -> CaptioningOutput:
        crops = input_data.get_crops()
        prompt = input_data.prompt or "<CAPTION>"
        
        generated_texts = []
        for i in range(0, len(crops), input_data.batch_size):
            batch = crops[i:i+input_data.batch_size]
            
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
            texts = self.processor.batch_decode(generated_ids, skip_special_tokens=True)
            generated_texts.extend(text.strip() for text in texts)
            
        return CaptioningOutput(captions=generated_texts) 
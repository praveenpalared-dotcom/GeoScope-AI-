import sys
import os
import torch
import torchvision.transforms.functional as F
import numpy as np
from safetensors.torch import load_file
from huggingface_hub import hf_hub_download
import time

# Insert the ml/btc directory into sys.path to allow importing the custom model modules
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BTC_DIR = os.path.join(BASE_DIR, 'ml', 'btc')
if BTC_DIR not in sys.path:
    sys.path.insert(0, BTC_DIR)

from models.modules.hf_backbone import HFBackbone
from models.modules.simple_diff import SubDiff
from models.modules.upernet import UperNetHead

class BTCModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        # Matches the BTC-B config
        self.encoder = HFBackbone(
            model_name='facebook/mask2former-swin-base-IN21k-cityscapes-semantic',
            return_layers=[1, 2, 3, 4],
            pretraining=False,
            train_args={'finetune': False, 'pretrained': False}
        )
        dims = self.encoder.get_out_dims()
        strides = self.encoder.get_strides()
        
        self.diff = SubDiff(dims=dims, pretraining=False)
        
        self.decoder = UperNetHead(
            input_sizes=dims,
            encoder_strides=strides,
            hidden_size=512,
            out_channels=1,
            pretraining=False
        )
        
    def forward(self, x1, x2):
        # Concatenate along batch dimension (N, C, H, W) -> (2N, C, H, W)
        x = torch.cat([x1, x2], dim=0)
        feat = self.encoder(x)
        diff_feat = self.diff(feat)
        
        # UperNetHead interpolates to self.out_size at the end
        self.decoder.out_size = x1.shape[2:]
        
        out = self.decoder(diff_feat)
        
        # The output might be for both or just the diff? 
        # The diff_feat has batch size N again because SubDiff chunks it and returns diffs.
        # So out will have batch size N.
        return out

# Global cache
_model_instance = None

def get_model() -> torch.nn.Module:
    global _model_instance
    if _model_instance is not None:
        return _model_instance
        
    print("Initializing BTC-B Model (Lazy Load)...")
    
    # 1. Download/Find the safetensors checkpoint
    ckpt_path = hf_hub_download(repo_id="blaz-r/BTC-B_oscd96", filename="model.safetensors")
    
    # 2. Instantiate the model
    model = BTCModel()
    
    # 3. Load the state dict
    state_dict = load_file(ckpt_path)
    
    # Clean keys if they have 'model.' prefix
    cleaned_dict = {}
    for k, v in state_dict.items():
        if k.startswith('model.'):
            cleaned_dict[k.replace('model.', '', 1)] = v
        else:
            cleaned_dict[k] = v
            
    # Remove any loss/metrics keys that might be in the checkpoint
    cleaned_dict = {k: v for k, v in cleaned_dict.items() if k.startswith(('encoder.', 'diff.', 'decoder.'))}
    
    missing, unexpected = model.load_state_dict(cleaned_dict, strict=False)
    if missing:
        print(f"Warning: Missing keys when loading BTC-B: {missing}")
        
    # 4. Prepare for CPU inference
    model.eval()
    _model_instance = model
    return _model_instance

def predict_change(before_rgb: np.ndarray, after_rgb: np.ndarray) -> np.ndarray:
    """
    Predict change probability given two RGB numpy arrays of shape (H, W, 3).
    Returns a probability map of shape (H, W).
    """
    start_time = time.time()
    
    # Ensure shape is (H, W, 3)
    if before_rgb.ndim != 3 or before_rgb.shape[-1] != 3:
        raise ValueError(f"Expected before_rgb to have shape (H, W, 3), got {before_rgb.shape}")
        
    H, W, _ = before_rgb.shape
    
    model = get_model()
    
    # Convert numpy arrays to torch tensors (C, H, W)
    if before_rgb.dtype == np.uint8:
        before_rgb = before_rgb.astype(np.float32) / 255.0
        after_rgb = after_rgb.astype(np.float32) / 255.0
    else:
        # Assuming float reflectance [0, 1] usually / 10000
        # If max is > 1.0, scale it down. Sentinel-2 L2A reflectance is usually 0-10000.
        if before_rgb.max() > 1.0:
            before_rgb = np.clip(before_rgb / 10000.0, 0.0, 1.0)
            after_rgb = np.clip(after_rgb / 10000.0, 0.0, 1.0)
        else:
            before_rgb = np.clip(before_rgb, 0.0, 1.0)
            after_rgb = np.clip(after_rgb, 0.0, 1.0)

    # Convert to tensor and permute to (C, H, W)
    t1 = torch.from_numpy(before_rgb).permute(2, 0, 1).float()
    t2 = torch.from_numpy(after_rgb).permute(2, 0, 1).float()
    
    # ImageNet Normalization
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]
    t1 = F.normalize(t1, mean=mean, std=std)
    t2 = F.normalize(t2, mean=mean, std=std)
    
    # Add batch dimension: (1, C, H, W)
    t1 = t1.unsqueeze(0)
    t2 = t2.unsqueeze(0)
    
    with torch.no_grad():
        logits = model(t1, t2)
        
    # Apply Sigmoid to get probability
    probs = torch.sigmoid(logits)
    
    # Remove batch and channel dims, convert back to numpy
    prob_map = probs.squeeze().cpu().numpy()
    
    end_time = time.time()
    print(f"BTC-B inference completed in {end_time - start_time:.2f} seconds.")
    
    return prob_map

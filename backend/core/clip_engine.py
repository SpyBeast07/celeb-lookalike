import torch
import open_clip
from PIL import Image
import numpy as np
import cv2

# Load CLIP model and preprocessing
# Using ViT-B-32 as requested
device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")
model = model.to(device)
model.eval()

def get_clip_embedding(img):
    """
    Extract normalized CLIP embedding from an image (numpy array).
    """
    # Convert numpy array (OpenCV format BGR) to PIL Image (RGB)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if len(img.shape) == 3 else img
    img_pil = Image.fromarray(img_rgb)
    
    # Preprocess and prepare for model
    img_tensor = preprocess(img_pil).unsqueeze(0).to(device)

    with torch.no_grad():
        # Encode and Normalize
        emb = model.encode_image(img_tensor)
        emb /= emb.norm(dim=-1, keepdim=True)

    # Return as numpy array for easier database storage/matching
    return emb.cpu().numpy().flatten()

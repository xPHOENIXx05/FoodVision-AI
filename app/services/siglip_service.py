import json
from pathlib import Path

import torch
from transformers import AutoModel, AutoProcessor

# Load the processor and model only once
MODEL_NAME = "google/siglip2-base-patch16-224"

processor = AutoProcessor.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
model.eval()

# Use GPU if available
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

# Load food labels
LABELS_PATH = Path("data/food_labels.json")

with open(LABELS_PATH, "r", encoding="utf-8") as f:
    FOOD_LABELS = json.load(f)

print(f"Loaded SigLIP2")
print(f"Device: {device}")
print(f"Food labels: {len(FOOD_LABELS)}")
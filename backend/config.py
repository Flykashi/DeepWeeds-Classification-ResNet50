"""Central configuration for the Weed Classification API.

Everything here mirrors the original research notebooks:
  * models/resnet50_final.keras   -> notebooks/resnet50_training.ipynb (cell 12)
  * 160x160 input                 -> img_size = (160, 160)
  * ResNet50 preprocess_input     -> tensorflow.keras.applications.resnet50
  * class order                   -> train_data.class_indices (alphabetical folders)
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# The trained model produced by the training notebook. Override with the
# WEED_MODEL_PATH environment variable if you keep it somewhere else.
MODEL_PATH = Path(os.getenv("WEED_MODEL_PATH", PROJECT_ROOT / "models" / "resnet50_final.keras"))

# Same as `img_size = (160, 160)` in resnet50_training.ipynb
IMG_SIZE = (160, 160)

# Exactly the `train_data.class_indices` printed by the training notebook
# (Keras flow_from_directory sorts class folders alphabetically).
CLASS_NAMES = [
    "Chinee apple",    # 0
    "Lantana",         # 1
    "Negative",        # 2
    "Parkinsonia",     # 3
    "Parthenium",      # 4
    "Prickly acacia",  # 5
    "Rubber vine",     # 6
    "Siam weed",       # 7
    "Snake weed",      # 8
    "Unknown",         # 9
]

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/pjpeg"}
MAX_UPLOAD_BYTES = int(os.getenv("WEED_MAX_UPLOAD_MB", "10")) * 1024 * 1024

# Browsers that open the frontend from another origin need CORS. The default
# is permissive because this is a local demo app; tighten for deployment.
CORS_ORIGINS = [o.strip() for o in os.getenv("WEED_CORS_ORIGINS", "*").split(",") if o.strip()]

# Keras' ImageDataGenerator.flow_from_directory (used for training and
# evaluation) resizes with PIL "nearest" by default, so we do the same.
RESIZE_METHOD = os.getenv("WEED_RESIZE_METHOD", "nearest").lower()

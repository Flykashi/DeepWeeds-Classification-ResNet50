"""Image preprocessing + inference, matching the original training pipeline."""
import io
import threading
from typing import Dict, List

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
from tensorflow.keras.applications.resnet50 import preprocess_input

from . import model_loader
from .config import CLASS_NAMES, IMG_SIZE, RESIZE_METHOD

_RESAMPLE = {
    "nearest": Image.NEAREST,
    "bilinear": Image.BILINEAR,
    "bicubic": Image.BICUBIC,
}.get(RESIZE_METHOD, Image.NEAREST)

_predict_lock = threading.Lock()


class InvalidImageError(ValueError):
    """Raised when the uploaded bytes are not a decodable JPG/PNG image."""


def preprocess_image(data: bytes) -> np.ndarray:
    """bytes -> float32 array of shape (1, 160, 160, 3) ready for ResNet50.

    Steps are the same as notebooks/evaluation.ipynb & resnet50_training.ipynb:
    RGB -> resize to 160x160 -> ResNet50 preprocess_input (no extra rescaling).
    """
    try:
        with Image.open(io.BytesIO(data)) as img:
            if img.format not in ("JPEG", "PNG"):
                raise InvalidImageError("Only JPG, JPEG and PNG images are supported.")
            img = ImageOps.exif_transpose(img)  # phone photos may be rotated via EXIF
            img = img.convert("RGB")
            img = img.resize((IMG_SIZE[1], IMG_SIZE[0]), _RESAMPLE)
            arr = np.asarray(img, dtype="float32")
    except InvalidImageError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise InvalidImageError("The file is not a valid image.") from exc
    return preprocess_input(np.expand_dims(arr, axis=0))


def predict(data: bytes) -> Dict:
    """Run the loaded model and return structured predictions."""
    model = model_loader.get_model()
    if model is None:
        raise RuntimeError(model_loader.load_error() or "Model is not loaded.")
    batch = preprocess_image(data)
    with _predict_lock:  # Keras models are not guaranteed thread-safe
        probs = np.asarray(model(batch, training=False))[0]

    ranked: List[Dict] = sorted(
        ({"class": name, "confidence": round(float(p) * 100.0, 2)} for name, p in zip(CLASS_NAMES, probs)),
        key=lambda item: item["confidence"],
        reverse=True,
    )
    top = ranked[0]
    return {
        "success": True,
        "predicted_class": top["class"],
        "confidence": top["confidence"],
        "predictions": ranked,
    }

"""Loads the existing trained ResNet50 model exactly once."""
import logging
from typing import Optional

from tensorflow.keras.models import load_model

from .config import CLASS_NAMES, IMG_SIZE, MODEL_PATH

logger = logging.getLogger("weed_api.model")

_model = None
_load_error: Optional[str] = None


def load() -> None:
    """Load the saved model from disk (called once at application start-up)."""
    global _model, _load_error
    if _model is not None:
        return
    if not MODEL_PATH.exists():
        _load_error = (
            f"Model file not found at '{MODEL_PATH}'. Place your trained "
            "'resnet50_final.keras' in the 'models/' folder (or set WEED_MODEL_PATH)."
        )
        logger.error(_load_error)
        return
    try:
        model = load_model(str(MODEL_PATH), compile=False)
        out_shape, in_shape = model.output_shape, model.input_shape
        if out_shape[-1] != len(CLASS_NAMES):
            raise ValueError(
                f"Model outputs {out_shape[-1]} classes but {len(CLASS_NAMES)} class names are configured."
            )
        if tuple(in_shape[1:3]) != tuple(IMG_SIZE):
            raise ValueError(f"Model expects input {in_shape} but preprocessing produces {IMG_SIZE}.")
        _model = model
        _load_error = None
        logger.info("Model loaded from %s (input %s, output %s)", MODEL_PATH, in_shape, out_shape)
    except Exception as exc:  # noqa: BLE001
        _load_error = f"Failed to load model: {exc}"
        logger.exception(_load_error)


def get_model():
    return _model


def is_loaded() -> bool:
    return _model is not None


def load_error() -> Optional[str]:
    return _load_error

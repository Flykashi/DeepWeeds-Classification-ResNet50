"""Integration tests for the FastAPI backend.

Run from the project root (requires models/resnet50_final.keras or WEED_MODEL_PATH):
    python -m pytest tests -q        (pip install pytest httpx)
    python tests/test_api.py         (no pytest needed)
"""
import io
import sys
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.main import app  # noqa: E402
from backend.config import CLASS_NAMES, MAX_UPLOAD_BYTES  # noqa: E402


def make_image(fmt="JPEG", size=(300, 200)) -> bytes:
    arr = np.random.RandomState(0).randint(0, 255, (size[1], size[0], 3), dtype="uint8")
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format=fmt)
    return buf.getvalue()


def run():
    with TestClient(app) as client:  # context manager triggers start-up (model load)
        r = client.get("/")
        assert r.status_code == 200 and r.json()["status"] == "running", r.text

        r = client.get("/health")
        assert r.status_code == 200 and r.json()["model_loaded"] is True, r.text

        for fmt, ctype, name in [("JPEG", "image/jpeg", "a.jpg"), ("PNG", "image/png", "a.png")]:
            r = client.post("/predict", files={"file": (name, make_image(fmt), ctype)})
            body = r.json()
            assert r.status_code == 200 and body["success"], r.text
            assert len(body["predictions"]) == len(CLASS_NAMES) == 10
            confs = [p["confidence"] for p in body["predictions"]]
            assert confs == sorted(confs, reverse=True)
            assert body["predicted_class"] == body["predictions"][0]["class"] in CLASS_NAMES
            assert abs(sum(confs) - 100) < 0.2, sum(confs)

        r = client.post("/predict", files={"file": ("a.txt", b"hello", "text/plain")})
        assert r.status_code == 415 and r.json()["success"] is False
        r = client.post("/predict", files={"file": ("fake.jpg", b"not really an image", "image/jpeg")})
        assert r.status_code == 400, r.text
        r = client.post("/predict", files={"file": ("empty.jpg", b"", "image/jpeg")})
        assert r.status_code == 400, r.text
        r = client.post("/predict", files={"file": ("big.jpg", b"0" * (MAX_UPLOAD_BYTES + 1), "image/jpeg")})
        assert r.status_code == 413, r.text
        r = client.post("/predict")
        assert r.status_code == 422
        r = client.get("/app/")
        assert r.status_code == 200 and "WeedVision" in r.text
    print("ALL API TESTS PASSED")


def test_api():
    run()


if __name__ == "__main__":
    run()

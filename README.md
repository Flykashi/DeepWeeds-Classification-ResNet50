# DeepWeeds Weed Classification — ResNet50 + FastAPI Web App

Original research project (TensorFlow/Keras, ResNet50 transfer learning on DeepWeeds, 10 classes, ~86 % test accuracy)
extended with a **FastAPI backend** and a **responsive web frontend** with image upload and live camera capture.
The original notebooks, results and model architecture are untouched.

## Project structure

```
├── notebooks/ , src/ , results/     original research code (unchanged)
├── models/                          put resnet50_final.keras here (git-ignored)
├── backend/
│   ├── main.py                      FastAPI app: GET /, GET /health, POST /predict, serves frontend at /app/
│   ├── model_loader.py              loads the existing .keras model once at start-up
│   ├── predictor.py                 preprocessing + inference (same as training/evaluation)
│   ├── config.py                    model path, 160x160 size, the 10 class names, limits, CORS
│   └── requirements.txt
├── frontend/                        index.html, style.css, script.js
├── tests/test_api.py                integration tests
├── run_app.bat                      one-click start on Windows
└── README.md
```

## Reused from the original project

| Item | Value (from your notebooks) |
|---|---|
| Model file | `models/resnet50_final.keras` (`resnet50_training.ipynb`, final save cell) |
| Input | 160 x 160 RGB |
| Preprocessing | `tensorflow.keras.applications.resnet50.preprocess_input`, no extra rescaling |
| Resize | PIL *nearest*, the default of `flow_from_directory` used for training and evaluation |
| Classes (index order) | Chinee apple, Lantana, Negative, Parkinsonia, Parthenium, Prickly acacia, Rubber vine, Siam weed, Snake weed, Unknown |

> The GitHub repository does not contain the trained model (`models/` and `*.keras` are in the original `.gitignore`).
> Copy **your own** `resnet50_final.keras` into the `models/` folder before running,
> or keep it elsewhere and set `WEED_MODEL_PATH`.

## Setup on Windows (CMD or PowerShell, Python 3.10-3.12)

```bat
cd path\to\DeepWeeds-Classification-ResNet50
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

Copy your model to `models\resnet50_final.keras`, then run:

```bat
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

(or double-click `run_app.bat` after setup). Open **http://127.0.0.1:8000/app/**.
API docs: http://127.0.0.1:8000/docs

Custom model location (CMD):

```bat
set WEED_MODEL_PATH=D:\models\resnet50_final.keras
python -m uvicorn backend.main:app --port 8000
```

Other env vars: `WEED_MAX_UPLOAD_MB` (default 10), `WEED_CORS_ORIGINS` (default `*`), `WEED_RESIZE_METHOD` (`nearest` default or `bilinear`).

## Using the app

* **Upload Image**: click or drag and drop a JPG/JPEG/PNG, preview it, remove with the X, press *Classify Weed*.
* **Live Camera**: *Start Camera* (allow the browser permission), *Switch Camera* (when several cameras exist), *Capture Image*, then *Classify Weed*.
  Camera access only works on `localhost`/HTTPS, so open `http://127.0.0.1:8000/app/` rather than double-clicking `index.html`.
* Results show the image, top class, a confidence bar, and all 10 classes sorted high to low.

Both sources use the same `POST /predict` endpoint.

## API

| Endpoint | Description |
|---|---|
| `GET /` | service status |
| `GET /health` | 200 if the model is loaded, 503 otherwise |
| `POST /predict` | multipart field `file` (JPG/JPEG/PNG, up to 10 MB) |

```bash
curl -F "file=@leaf.jpg" http://127.0.0.1:8000/predict
```
```json
{"success": true, "predicted_class": "Parkinsonia", "confidence": 96.45,
 "predictions": [{"class": "Parkinsonia", "confidence": 96.45}, "... 10 items, sorted"]}
```
Errors return `{"success": false, "error": "..."}` with 400 (invalid/empty image), 413 (too large), 415 (wrong type), 503 (model not loaded).

## Tests

```bat
pip install pytest httpx
python -m pytest tests -q
```

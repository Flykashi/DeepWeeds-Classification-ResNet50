"""FastAPI application exposing the existing ResNet50 weed classifier.

Run from the project root:
    uvicorn backend.main:app --host 127.0.0.1 --port 8000
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import model_loader, predictor
from .config import (
    ALLOWED_CONTENT_TYPES,
    ALLOWED_EXTENSIONS,
    CLASS_NAMES,
    CORS_ORIGINS,
    MAX_UPLOAD_BYTES,
    MODEL_PATH,
    PROJECT_ROOT,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("weed_api")

FRONTEND_DIR = PROJECT_ROOT / "frontend"


@asynccontextmanager
async def lifespan(_: FastAPI):
    model_loader.load()  # load the model ONE time at start-up
    yield


app = FastAPI(
    title="Weed Classification API",
    description="FastAPI service for the DeepWeeds ResNet50 (TensorFlow/Keras) classifier.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def error(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"success": False, "error": message})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException):
    return error(exc.status_code, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return error(422, "Invalid request. Send the image as multipart/form-data in the 'file' field.")


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    logger.exception("Unhandled error")
    return error(500, "Internal server error.")


@app.get("/")
async def root():
    return {
        "success": True,
        "service": "Weed Classification API",
        "status": "running",
        "model_loaded": model_loader.is_loaded(),
        "num_classes": len(CLASS_NAMES),
        "docs": "/docs",
        "frontend": "/app/" if FRONTEND_DIR.exists() else None,
    }


@app.get("/health")
async def health():
    loaded = model_loader.is_loaded()
    body = {
        "success": loaded,
        "status": "ok" if loaded else "model_not_loaded",
        "model_loaded": loaded,
        "model_path": str(MODEL_PATH),
        "classes": CLASS_NAMES,
    }
    if not loaded:
        body["detail"] = model_loader.load_error()
    return JSONResponse(status_code=200 if loaded else 503, content=body)


async def read_limited(file: UploadFile) -> bytes:
    """Asynchronously read the upload, aborting as soon as it exceeds the size limit."""
    chunks, size = [], 0
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        size += len(chunk)
        if size > MAX_UPLOAD_BYTES:
            raise HTTPException(413, f"Image is too large. Maximum size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
        chunks.append(chunk)
    return b"".join(chunks)


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not model_loader.is_loaded():
        raise HTTPException(503, model_loader.load_error() or "Model is not loaded.")

    name = (file.filename or "").lower()
    ext = Path(name).suffix
    if file.content_type not in ALLOWED_CONTENT_TYPES and ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, "Unsupported file type. Please upload a JPG, JPEG or PNG image.")

    data = await read_limited(file)
    if not data:
        raise HTTPException(400, "The uploaded file is empty.")

    try:
        result = await run_in_threadpool(predictor.predict, data)
    except predictor.InvalidImageError as exc:
        raise HTTPException(400, str(exc))
    return result


if FRONTEND_DIR.exists():
    # Serving the UI from the same origin as the API keeps camera access (a
    # "secure context" on localhost) and CORS trouble-free.
    app.mount("/app", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

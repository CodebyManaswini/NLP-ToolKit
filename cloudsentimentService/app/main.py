"""
Sentiment Analysis Service
---------------------------
Standalone FastAPI microservice that wraps a pretrained DistilBERT
sentiment model (SST-2 fine-tuned) behind a simple REST API.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from transformers import pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentiment-service")

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"

_model_state = {"pipeline": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the model once at startup, not per-request."""
    logger.info(f"Loading model: {MODEL_NAME}")
    start = time.time()
    _model_state["pipeline"] = pipeline(
        task="sentiment-analysis",
        model=MODEL_NAME,
        tokenizer=MODEL_NAME,
    )
    logger.info(f"Model loaded in {time.time() - start:.2f}s")
    yield
    _model_state["pipeline"] = None


app = FastAPI(
    title="Sentiment Analysis Service",
    description="Standalone microservice for text sentiment inference (DistilBERT/SST-2).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class PredictResponse(BaseModel):
    text: str
    label: str
    confidence: float
    inference_time_ms: float


class HealthResponse(BaseModel):
    status: str
    model: str
    model_loaded: bool


@app.get("/health", response_model=HealthResponse)
def health():
    loaded = _model_state["pipeline"] is not None
    return HealthResponse(
        status="ok" if loaded else "starting",
        model=MODEL_NAME,
        model_loaded=loaded,
    )


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    clf = _model_state["pipeline"]
    if clf is None:
        raise HTTPException(status_code=503, detail="Model is still loading, try again shortly.")

    start = time.time()
    try:
        result = clf(request.text)[0]
    except Exception as e:
        logger.exception("Inference failed")
        raise HTTPException(status_code=500, detail=f"Inference error: {e}")
    elapsed_ms = (time.time() - start) * 1000

    return PredictResponse(
        text=request.text,
        label=result["label"],
        confidence=round(result["score"], 4),
        inference_time_ms=round(elapsed_ms, 2),
    )


@app.get("/")
def root():
    return {"service": "sentiment-analysis-service", "endpoints": ["/predict (POST)", "/health (GET)"]}
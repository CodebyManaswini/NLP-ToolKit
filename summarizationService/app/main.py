"""
Document Summarization Service
---------------------------------
Accepts an uploaded document (PDF/DOCX/TXT), extracts its text, and
returns an abstractive summary using a distilled BART model. Long
documents are handled via map-reduce chunking (see summarizer.py).
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline

from app.extraction import EmptyDocumentError, UnsupportedFileType, extract_text
from app.summarizer import summarize_document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("summarization-service")

MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = (".pdf", ".docx", ".txt")

_model_state = {"pipeline": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Loading model: {MODEL_NAME}")
    start = time.time()
    _model_state["pipeline"] = pipeline("summarization", model=MODEL_NAME, tokenizer=MODEL_NAME)
    logger.info(f"Model loaded in {time.time() - start:.2f}s")
    yield
    _model_state["pipeline"] = None


app = FastAPI(
    title="Document Summarization Service",
    description="Uploads a PDF/DOCX/TXT file and returns an abstractive summary.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SummarizeResponse(BaseModel):
    filename: str
    original_word_count: int
    summary: str
    summary_word_count: int
    chunk_count: int
    chunk_summaries: list[str] | None
    processing_time_ms: float


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


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 10MB).")
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        text = extract_text(file.filename, file_bytes)
    except UnsupportedFileType as e:
        raise HTTPException(status_code=415, detail=str(e))
    except EmptyDocumentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Text extraction failed")
        raise HTTPException(status_code=422, detail=f"Could not extract text: {e}")

    summarizer = _model_state["pipeline"]
    if summarizer is None:
        raise HTTPException(status_code=503, detail="Model is still loading, try again shortly.")

    start = time.time()
    try:
        result = summarize_document(text, summarizer)
    except Exception as e:
        logger.exception("Summarization failed")
        raise HTTPException(status_code=500, detail=f"Summarization error: {e}")
    elapsed_ms = (time.time() - start) * 1000

    return SummarizeResponse(
        filename=file.filename,
        original_word_count=len(text.split()),
        summary=result["summary"],
        summary_word_count=len(result["summary"].split()),
        chunk_count=result["chunk_count"],
        chunk_summaries=result["chunk_summaries"],
        processing_time_ms=round(elapsed_ms, 2),
    )


@app.get("/")
def root():
    return {
        "service": "summarization-service",
        "endpoints": ["/summarize (POST, multipart file upload)", "/health (GET)"],
        "allowed_file_types": ALLOWED_EXTENSIONS,
    }
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

from .routers import documents, ocr
from .whatsapp import router as whatsapp_router

app = FastAPI(
    title="OCR Service with Gemini Vision API",
    description="API de procesamiento OCR para boletas y facturas usando Google Gemini Vision",
    version="2.0.0"
)

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(ocr.router)
app.include_router(whatsapp_router.router)

@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "OCR Service",
        "version": "2.0.0",
        "engine": "Gemini Vision API"
    }

@app.get("/")
def root():
    return {
        "message": "OCR Service con Gemini Vision API",
        "docs": "/docs",
        "health": "/health"
    }

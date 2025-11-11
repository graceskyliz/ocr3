from fastapi import FastAPI
from .routers import documents, ocr

app = FastAPI(title="OCR Service")
app.include_router(documents.router)
app.include_router(ocr.router)

@app.get("/health")
def health():
    return {"ok": True}

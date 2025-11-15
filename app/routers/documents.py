from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from ..settings import settings
from ..db import SessionLocal
from ..models import Document
from ..storage_local import save_file_local, sha256_bytes
import uuid
import io
from sqlalchemy import text

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = Form(...),
    user_id: str | None = Form(None),
    doc_kind: str = Form(...),  # 'boleta' | 'factura' | 'excel'
):
    """
    Endpoint para subir documentos (PDF, JPG, PNG) para procesamiento OCR.
    Los archivos se guardan localmente en el servidor.
    """
    if file.content_type not in settings.ALLOWED_MIME:
        raise HTTPException(status_code=415, detail="MIME no permitido")

    raw = await file.read()
    if len(raw) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Archivo muy grande")

    # Deducir formato fuente
    name = (file.filename or "").lower()
    if name.endswith(".xlsx") or name.endswith(".xls"):
        source_format = "xlsx"
    elif name.endswith(".pdf"):
        source_format = "pdf"
    elif name.endswith((".jpg", ".jpeg")):
        source_format = "jpg"
    elif name.endswith(".png"):
        source_format = "png"
    else:
        source_format = "bin"

    doc_id = uuid.uuid4()
    
    # Guardar archivo localmente
    storage_key = save_file_local(io.BytesIO(raw), tenant_id, str(doc_id), file.filename)

    with SessionLocal() as db:
        # Insertar registro en base de datos
        db.execute(
            text("""
                INSERT INTO documents.documents
                  (id, tenant_id, user_id, filename, storage_key, mime, size, sha256, status, doc_kind, source_format)
                VALUES
                  (:id, :tenant, :user, :fn, :key, :mime, :size, :sha, 'uploaded', :kind, :fmt)
            """),
            {
                "id": str(doc_id),
                "tenant": tenant_id,
                "user": user_id,
                "fn": file.filename,
                "key": storage_key,
                "mime": file.content_type,
                "size": len(raw),
                "sha": sha256_bytes(raw),
                "kind": doc_kind,
                "fmt": source_format,
            },
        )
        db.commit()

    return {
        "id": str(doc_id), 
        "storage_key": storage_key,
        "message": "Documento subido exitosamente. Use /ocr/process/{doc_id} para procesarlo."
    }

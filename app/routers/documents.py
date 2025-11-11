from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from ..config import settings
from ..db import SessionLocal
from ..models import Document
from ..s3_client import put_file, sha256_bytes
import uuid, io

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = Form(...),
    user_id: str | None = Form(None)
):
    if file.content_type not in settings.ALLOWED_MIME:
        raise HTTPException(status_code=415, detail="MIME no permitido")
    raw = await file.read()
    if len(raw) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Archivo muy grande")

    doc_id = uuid.uuid4()
    key = f"{settings.S3_PREFIX}{tenant_id}/{doc_id}/{file.filename}"
    put_file(io.BytesIO(raw), key)

    with SessionLocal() as db:
        d = Document(
            id=doc_id,
            tenant_id=uuid.UUID(tenant_id),
            user_id=uuid.UUID(user_id) if user_id else None,
            filename=file.filename,
            storage_key=key,
            mime=file.content_type,
            size=len(raw),
            sha256=sha256_bytes(raw),
            status="uploaded"
        )
        db.add(d)
        db.commit()

    return {"id": str(doc_id), "storage_key": key}

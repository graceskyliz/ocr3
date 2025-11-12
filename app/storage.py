# app/storage.py
import os
import uuid
import tempfile
import boto3
from botocore.exceptions import ClientError
from sqlalchemy import text
from fastapi import HTTPException

# Si tienes settings, úsalo para región; si no, ignóralo sin romper
try:
    from app.settings import settings
    _REGION = getattr(settings, "AWS_REGION", None)
except Exception:
    settings = None
    _REGION = None

def s3_client():
    return boto3.client("s3", region_name=_REGION) if _REGION else boto3.client("s3")

def download_to_tmp(bucket: str, key: str) -> str:
    if not bucket or not key:
        raise ValueError("bucket y key son obligatorios")
    _, ext = os.path.splitext(key)
    local_path = os.path.join(tempfile.gettempdir(), f"ocr_{uuid.uuid4().hex}{ext or ''}")
    try:
        s3_client().download_file(bucket, key, local_path)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code in ("NoSuchKey", "404"):
            raise HTTPException(status_code=404, detail=f"S3 key no encontrada: s3://{bucket}/{key}")
        raise HTTPException(status_code=502, detail=f"Fallo descargando de S3: {e}")
    if not os.path.exists(local_path) or os.path.getsize(local_path) == 0:
        raise HTTPException(status_code=500, detail="Descarga S3 vacía o corrupta")
    return local_path

def _looks_like_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False

def get_s3_key_for_document(identifier: str, db, default_bucket: str | None = None):
    """
    Si 'identifier' es UUID -> consulta en BD el storage_key.
    Si NO es UUID -> asume que 'identifier' YA es el storage_key (no consulta BD).
    Devuelve SOLO el storage_key para compatibilidad con código existente.
    """
    if _looks_like_uuid(identifier):
        row = db.execute(
            text("SELECT storage_key FROM documents.documents WHERE id = :id"),
            {"id": identifier}
        ).fetchone()
        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Documento no encontrado o sin storage_key")
        return row[0]
    else:
        # Es un path tipo 'uploads/.../archivo.ext' -> úsalo tal cual
        return identifier

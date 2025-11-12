# app/storage.py
import os
import uuid
import tempfile
import boto3
from botocore.exceptions import ClientError
from sqlalchemy import text
from fastapi import HTTPException
from app.settings import settings

def s3_client():
    # Usa la región de settings si existe, si no deja que boto3 la resuelva
    region = getattr(settings, "AWS_REGION", None)
    return boto3.client("s3", region_name=region) if region else boto3.client("s3")

def download_to_tmp(bucket: str, key: str) -> str:
    """
    Descarga un objeto S3 a /tmp y devuelve la ruta local.
    Crea un nombre de archivo seguro preservando la extensión.
    """
    if not bucket or not key:
        raise ValueError("bucket y key son obligatorios")

    _, ext = os.path.splitext(key)
    # Nombre predecible pero único
    local_name = f"ocr_{uuid.uuid4().hex}{ext or ''}"
    local_path = os.path.join(tempfile.gettempdir(), local_name)

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

def get_s3_key_for_document(identifier: str, db):
    """
    Si te pasan un UUID (id de documents.documents) -> consulta storage_key.
    Si te pasan un path S3 (uploads/.../archivo.ext) -> lo devuelve tal cual.
    """
    from uuid import UUID
    try:
        UUID(str(identifier))
        row = db.execute(
            text("SELECT storage_key FROM documents.documents WHERE id = :id"),
            {"id": identifier}
        ).fetchone()
        if not row or not row[0]:
            raise HTTPException(status_code=404, detail="Documento no encontrado o sin storage_key")
        return row[0]
    except Exception:
        # No es UUID, asumimos que ya es un storage_key
        return identifier

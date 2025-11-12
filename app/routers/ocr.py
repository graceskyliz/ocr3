# app/routers/ocr.py
from uuid import UUID
from typing import Dict, Any, Optional
import logging
import os

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.settings import settings
from ..db import SessionLocal
from ..storage import download_to_tmp
from ..finance_mapper import materialize_invoice
# from ..textract_client import analyze_expense_s3  # futuro

from ..ocr_local import (
    parse_excel_local,
    extract_text,
    autodetect_kind,
    parse_boleta_local,
    parse_factura_local,
)

router = APIRouter(prefix="/ocr", tags=["ocr"])
log = logging.getLogger(__name__)


@router.post("/process/{doc_id}")
def process_document(doc_id: str) -> Dict[str, Any]:
    """
    Procesa un documento subido a S3 (clave en storage_key).
    Descarga a /tmp, detecta tipo (boleta/factura/excel) y persiste la invoice.
    """

    # 0) Validaciones tempranas
    try:
        UUID(str(doc_id))
    except Exception:
        raise HTTPException(status_code=400, detail="doc_id no es un UUID válido")

    # Bucket: usa S3_BUCKET (variable real de entorno)
    s3_bucket = getattr(settings, "S3_BUCKET", None)
    if not s3_bucket:
        # fallback por si quieres soportar ambos nombres de env
        s3_bucket = os.getenv("S3_BUCKET") or os.getenv("INGEST_BUCKET")
    if not s3_bucket:
        raise HTTPException(
            status_code=500,
            detail="S3_BUCKET no está configurado (define la variable de entorno o usa settings.py)",
        )

    local_path: Optional[str] = None

    with SessionLocal() as db:
        # 1) Metadatos del documento
        doc = db.execute(
            text(
                """
                SELECT id::text, tenant_id::text, storage_key, doc_kind, source_format
                FROM documents.documents
                WHERE id = :id
                """
            ),
            {"id": doc_id},
        ).mappings().first()

        if not doc:
            raise HTTPException(status_code=404, detail="document not found")

        storage_key = (doc.get("storage_key") or "").strip()
        if not storage_key:
            raise HTTPException(status_code=422, detail="documento sin storage_key")

        # 2) Descargar desde S3 a /tmp
        try:
            local_path = download_to_tmp(s3_bucket, storage_key)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Fallo al descargar de S3: {e}")

        try:
            # 3) Determinar tipo y parsear
            kind = (doc.get("doc_kind") or "").lower()
            fmt = (doc.get("source_format") or "").lower()

            # heurística extra: por extensión
            ext = os.path.splitext(storage_key)[1].lower().lstrip(".")

            is_excel = (kind == "excel") or (fmt in {"xls", "xlsx"}) or (ext in {"xls", "xlsx"})
            if is_excel:
                result = parse_excel_local(local_path)
                engine = "local-excel"
            else:
                raw = extract_text(local_path)
                if not kind:
                    kind = (autodetect_kind(raw) or "factura").lower()

                if kind == "boleta":
                    result = parse_boleta_local(raw)
                else:
                    result = parse_factura_local(raw)
                    kind = "factura"  # normaliza

                engine = "local-tesseract"

            # 4) Persistir invoice
            inv_id = materialize_invoice(db, doc_id, engine, result)

            # 5) Guardar tipo en la invoice (si aplica)
            db.execute(
                text(
                    """
                    UPDATE finance.invoices
                    SET doc_kind = :k
                    WHERE id = :inv_id
                    """
                ),
                {
                    "k": kind if kind in ("boleta", "factura", "excel") else None,
                    "inv_id": str(inv_id),
                },
            )
            db.commit()

            # log mínimo para trazabilidad
            log.info("ocr.process ok doc_id=%s engine=%s kind=%s", doc_id, engine, kind)

            return {
                "engine": engine,
                "doc_kind": kind,
                "invoice_id": str(inv_id),
                "confidence": (result or {}).get("confidence"),
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OCR/parse failed: {e}")
        finally:
            # 6) Limpieza de /tmp
            if local_path:
                try:
                    if os.path.exists(local_path):
                        os.remove(local_path)
                except Exception:
                    pass

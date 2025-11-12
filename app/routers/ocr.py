# app/routers/ocr.py
from uuid import UUID
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.settings import settings
from ..db import SessionLocal
from ..storage import download_to_tmp
from ..finance_mapper import materialize_invoice

# Mantén este import para futuro (Textract en S3) si luego migras a AWS:
# from ..textract_client import analyze_expense_s3

# Funciones locales de OCR/parsing
from ..ocr_local import (
    parse_excel_local,
    extract_text,
    autodetect_kind,
    parse_boleta_local,
    parse_factura_local,
)

router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.post("/process/{doc_id}")
def process_document(doc_id: str) -> Dict[str, Any]:
    """
    Procesa un documento ya subido a S3 (indicado por storage_key en BD).
    Descarga a /tmp, detecta tipo (boleta/factura/excel) y persiste la invoice.
    """

    # (Opcional) valida que el id tenga forma de UUID para evitar consultas inválidas
    try:
        UUID(str(doc_id))
    except Exception:
        raise HTTPException(status_code=400, detail="doc_id no es un UUID válido")

    # Valida configuración mínima
    ingest_bucket = getattr(settings, "INGEST_BUCKET", None)
    if not ingest_bucket:
        raise HTTPException(
            status_code=500,
            detail="INGEST_BUCKET no está configurado (define la variable de entorno o usa settings.py)",
        )

    local_path: Optional[str] = None

    with SessionLocal() as db:
        # 1) Traer metadatos del documento
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

        storage_key = doc.get("storage_key")
        if not storage_key:
            raise HTTPException(status_code=422, detail="documento sin storage_key")

        # 2) Descargar a /tmp desde S3
        try:
            local_path = download_to_tmp(ingest_bucket, storage_key)
        except HTTPException:
            # Errores controlados (404 NoSuchKey, etc.)
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Fallo al descargar de S3: {e}")

        try:
            # 3) Determinar tipo/parsear
            kind = (doc.get("doc_kind") or "").lower()
            fmt = (doc.get("source_format") or "").lower()

            if kind == "excel" or fmt == "xlsx":
                # Parseo de Excel local
                result = parse_excel_local(local_path)
                engine = "local-excel"
            else:
                # OCR + parsing
                raw = extract_text(local_path)

                if not kind:
                    kind = (autodetect_kind(raw) or "factura").lower()

                if kind == "boleta":
                    result = parse_boleta_local(raw)
                else:
                    # Por defecto, factura
                    result = parse_factura_local(raw)

                engine = "local-tesseract"

            # 4) Materializar invoice en módulo de finanzas
            inv_id = materialize_invoice(db, doc_id, engine, result)

            # 5) (Opcional) Persistir el tipo detectado en la invoice
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

            # 6) Respuesta
            return {
                "engine": engine,
                "doc_kind": kind,
                "invoice_id": str(inv_id),
                "confidence": (result or {}).get("confidence"),
            }

        except HTTPException:
            # Propaga errores de FastAPI tal cual
            raise
        except Exception as e:
            # Cualquier error no controlado del pipeline
            raise HTTPException(status_code=500, detail=f"OCR/parse failed: {e}")
        finally:
            # 7) Limpieza de /tmp aunque falle algo
            if local_path:
                try:
                    import os
                    if os.path.exists(local_path):
                        os.remove(local_path)
                except Exception:
                    # No bloquear por cleanup
                    pass

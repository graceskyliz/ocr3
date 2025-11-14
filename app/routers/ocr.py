# app/routers/ocr.py
from uuid import UUID
from typing import Dict, Any, Optional
import logging
import os

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.settings import settings
from ..db import SessionLocal
from ..storage_local import get_file_path
from ..finance_mapper import materialize_invoice
from ..gemini_client import (
    configure_gemini, 
    analyze_document_gemini, 
    analyze_pdf_with_gemini
)

router = APIRouter(prefix="/ocr", tags=["ocr"])
log = logging.getLogger(__name__)

# Configurar Gemini al iniciar el router
configure_gemini(settings.GEMINI_API_KEY)


@router.post("/process/{doc_id}")
def process_document(doc_id: str) -> Dict[str, Any]:
    """
    Procesa un documento subido localmente usando Gemini Vision API.
    Extrae información de boletas, facturas o documentos financieros.
    
    El resultado se puede enviar posteriormente a tu microservicio 'insights' para análisis con IA.
    """

    # 0) Validaciones tempranas
    try:
        UUID(str(doc_id))
    except Exception:
        raise HTTPException(status_code=400, detail="doc_id no es un UUID válido")

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

        # 2) Obtener ruta local del archivo
        try:
            local_path = get_file_path(storage_key)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Fallo al obtener archivo: {e}")

        try:
            # 3) Determinar tipo y procesar con Gemini
            kind = (doc.get("doc_kind") or "").lower()
            fmt = (doc.get("source_format") or "").lower()

            # Heurística extra: por extensión
            ext = os.path.splitext(storage_key)[1].lower().lstrip(".")

            # Determinar tipo de documento (por defecto factura si no se especificó)
            if not kind:
                kind = "factura"
            
            # Validar que no sea Excel (no soportado con Gemini Vision)
            is_excel = (kind == "excel") or (fmt in {"xls", "xlsx"}) or (ext in {"xls", "xlsx"})
            if is_excel:
                raise HTTPException(
                    status_code=422, 
                    detail="Archivos Excel no son soportados en esta versión. Use solo PDF, JPG o PNG."
                )

            # 4) Procesar con Gemini Vision API
            if fmt == "pdf" or ext == "pdf":
                result = analyze_pdf_with_gemini(local_path, kind)
            else:
                result = analyze_document_gemini(local_path, kind)

            engine = result.get("engine", "gemini-vision")

            # 5) Persistir invoice
            inv_id = materialize_invoice(db, doc_id, engine, result)

            # 6) Guardar tipo en la invoice (si aplica)
            db.execute(
                text(
                    """
                    UPDATE finance.invoices
                    SET doc_kind = :k
                    WHERE id = :inv_id
                    """
                ),
                {
                    "k": kind if kind in ("boleta", "factura") else None,
                    "inv_id": str(inv_id),
                },
            )
            db.commit()

            # Log para trazabilidad
            log.info("ocr.process ok doc_id=%s engine=%s kind=%s", doc_id, engine, kind)

            # Obtener datos parseados para respuesta
            parsed_data = result.get("parsed", {})

            return {
                "engine": engine,
                "doc_kind": kind,
                "invoice_id": str(inv_id),
                "confidence": result.get("confidence"),
                "data": parsed_data,
                "message": "OCR procesado exitosamente. Los datos están listos para enviar al microservicio 'insights'."
            }

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error procesando documento {doc_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"OCR/parse failed: {e}")

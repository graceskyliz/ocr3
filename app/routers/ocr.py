# fragmento clave de app/routers/ocr.py
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from ..ocr_local import analyze_file_local
from ..textract_client import analyze_expense_s3   # lo mantienes para futuro
from ..db import SessionLocal
from ..finance_mapper import materialize_invoice
from ..storage import get_s3_key_for_document

router = APIRouter(prefix="/ocr", tags=["ocr"])

@router.post("/process/{doc_id}")
def process_document(doc_id: str):
    with SessionLocal() as db:
        doc = db.execute(text("""
            SELECT id::text, tenant_id::text, storage_key, doc_kind, source_format
            FROM documents.documents
            WHERE id = :id
        """), {"id": doc_id}).mappings().first()
        if not doc:
            raise HTTPException(404, "document not found")

        bucket, key = get_s3_key_for_document(doc["storage_key"])  # adapta si tu helper es distinto
        local_path = download_to_tmp(bucket, key)                   # guarda en /tmp

        kind = (doc["doc_kind"] or "").lower()
        fmt  = (doc["source_format"] or "").lower()

        if kind == "excel" or fmt == "xlsx":
            result = parse_excel_local(local_path)
            engine = "local-excel"
        else:
            raw = extract_text(local_path)
            if not kind:
                kind = autodetect_kind(raw) or "factura"
            if kind == "boleta":
                result = parse_boleta_local(raw)
            else:
                result = parse_factura_local(raw)
            engine = "local-tesseract"

        inv_id = materialize_invoice(db, doc_id, engine, result)
        # opcional: guarda el tipo en la invoice
        db.execute(
            text("""
                UPDATE finance.invoices SET doc_kind=:k WHERE id=:inv_id
            """), {"k": kind if kind in ("boleta","factura") else None, "inv_id": str(inv_id)})
        db.commit()

        return {"engine": engine, "doc_kind": kind, "invoice_id": str(inv_id), "confidence": result.get("confidence")}
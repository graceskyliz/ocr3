from fastapi import APIRouter, HTTPException
from ..config import settings
from ..db import SessionLocal
from ..models import Document, Extraction
from ..finance_mapper import materialize_invoice
from ..textract_client import analyze_expense_s3
from ..s3_client import get_object_bytes
import boto3, uuid

router = APIRouter(prefix="/ocr", tags=["ocr"])
s3 = boto3.client("s3", region_name=settings.AWS_REGION)

def _bk(storage_key: str):  # bucket, key
    return settings.S3_BUCKET, storage_key

@router.post("/process/{document_id}")
def process_document(document_id: str):
    with SessionLocal() as db:
        doc = db.get(Document, uuid.UUID(document_id))
        if not doc:
            raise HTTPException(404, "Documento no encontrado")

        bucket, key = _bk(doc.storage_key)

        if doc.mime in ("application/pdf", "image/jpeg", "image/png"):
            result = analyze_expense_s3(bucket, key)
            engine = "textract-analyze-expense"
        elif doc.mime == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            raw = get_object_bytes(key)
            from ..excel_parser import parse_invoice_xlsx
            result = parse_invoice_xlsx(raw)
            engine = "xlsx-parser"
        else:
            raise HTTPException(415, "MIME no soportado")

        ext = Extraction(
            id=uuid.uuid4(), document_id=doc.id, engine=engine,
            json=result, confidence=result.get("confidence"), status="ok"
        )
        db.add(ext)

        # MATERIALIZAR EN FINANCE.*
        invoice_id = materialize_invoice(db, doc.tenant_id, doc.id, result)

        doc.status = "processed"
        db.commit()

    return {"extraction_id": str(ext.id), "engine": engine,
            "confidence": result.get("confidence"), "invoice_id": str(invoice_id)}

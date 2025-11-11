# fragmento clave de app/routers/ocr.py
import os, tempfile, boto3
from fastapi import APIRouter, HTTPException
from ..ocr_local import analyze_file_local
from ..textract_client import analyze_expense_s3   # lo mantienes para futuro
from ..db import SessionLocal
from ..finance_mapper import materialize_invoice
from ..storage import get_s3_key_for_document

router = APIRouter(prefix="/ocr", tags=["ocr"])

@router.post("/process/{doc_id}")
def process_document(doc_id: str):
    engine = os.getenv("OCR_ENGINE", "textract").lower()
    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION","us-east-1"))
    bucket, key = get_s3_key_for_document(doc_id)

    with tempfile.NamedTemporaryFile(suffix=os.path.splitext(key)[1], delete=True) as tmp:
        s3.download_file(bucket, key, tmp.name)

        if engine == "local":
            result = analyze_file_local(tmp.name)
        else:
            # Cuando habilites Textract, bastará con OCR_ENGINE=textract
            result = analyze_expense_s3(bucket, key)

    with SessionLocal() as db:
        inv_id = materialize_invoice(db, doc_id, result)

    return {"engine": result["engine"], "confidence": result["confidence"], "invoice_id": str(inv_id)}

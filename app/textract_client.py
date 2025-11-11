import boto3
from .config import settings

tx = boto3.client("textract", region_name=settings.AWS_REGION)

def analyze_expense_s3(bucket: str, key: str) -> dict:
    resp = tx.analyze_expense(Document={"S3Object": {"Bucket": bucket, "Name": key}})
    fields, items, confidences = {}, [], []
    for doc in resp.get("ExpenseDocuments", []):
        for f in doc.get("SummaryFields", []):
            label = (f.get("LabelDetection") or {}).get("Text") or (f.get("Type") or {}).get("Text") or ""
            value = (f.get("ValueDetection") or {}).get("Text") or ""
            conf  = (f.get("ValueDetection") or {}).get("Confidence") or 0.0
            if label:
                fields[label.strip().lower()] = value
                confidences.append(conf)
        for group in doc.get("LineItemGroups", []):
            for line in group.get("LineItems", []):
                row = {}
                for fe in line.get("LineItemExpenseFields", []):
                    k = (fe.get("LabelDetection") or {}).get("Text") or (fe.get("Type") or {}).get("Text") or ""
                    v = (fe.get("ValueDetection") or {}).get("Text") or ""
                    if k:
                        row[k.strip().lower()] = v
                if row: items.append(row)
    conf = sum(confidences)/len(confidences) if confidences else None
    return {"fields": fields, "items": items, "confidence": conf}

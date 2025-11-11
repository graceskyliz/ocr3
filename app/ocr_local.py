# app/ocr_local.py
import os, re
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

def _images_from_pdf(pdf_path: str) -> List[Image.Image]:
    # convierte cada página a imagen (usa poppler)
    return convert_from_path(pdf_path, dpi=300)

def _text_from_image(img: Image.Image) -> str:
    # español + inglés
    return pytesseract.image_to_string(img, lang="spa+eng")

def _parse_invoice_text(text: str) -> Dict[str, Any]:
    # Heurísticas simples (ajústalas a tu formato/país)
    date = None
    for pat, fmt in [(r"(\d{2}/\d{2}/\d{4})","%d/%m/%Y"), (r"(\d{4}-\d{2}-\d{2})","%Y-%m-%d")]:
        m = re.search(pat, text)
        if m:
            try:
                date = datetime.strptime(m.group(1), fmt).date()
                break
            except: pass

    total = None
    m = re.search(r"TOTAL(?:\s*[:=])?\s*S?/?\s*([0-9\.,]+)", text, re.IGNORECASE)
    if m:
        v = m.group(1).replace(".", "").replace(",", ".")
        try: total = Decimal(v)
        except: total = None

    ruc = None
    m = re.search(r"(RUC|N\.?R\.?U\.?C\.?)\s*[:\-]?\s*([0-9]{8,14})", text, re.IGNORECASE)
    if m: ruc = m.group(2)

    return {
        "provider": {"ruc": ruc, "razon_social": None},
        "invoice":  {"fecha": f"{date}" if date else None, "moneda": None, "total": str(total) if total else None},
        "items": []
    }

def analyze_file_local(local_path: str) -> Dict[str, Any]:
    pages_text: List[str] = []
    if local_path.lower().endswith(".pdf"):
        for im in _images_from_pdf(local_path):
            pages_text.append(_text_from_image(im))
    else:
        pages_text.append(_text_from_image(Image.open(local_path)))

    full_text = "\n".join(pages_text)
    parsed = _parse_invoice_text(full_text)
    conf = min(0.99, max(0.1, len(full_text) / 5000.0))  # proxy de “confianza”
    return {"engine": "local-tesseract", "confidence": float(conf), "raw_text": full_text[:20000], "parsed": parsed}

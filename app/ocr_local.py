# app/ocr_local.py
import os, re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Any, Optional, Tuple
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

# ------------ Utilidades de normalización ------------

DEC_SEP_RE = re.compile(r"[.,]")

def _to_decimal(txt: Optional[str]) -> Optional[Decimal]:
    if not txt:
        return None
    # normaliza separadores decimales: acepta "1.234,56" o "1,234.56" o "1234.56"
    t = txt.strip()
    # elimina espacios y monedas sueltas
    t = re.sub(r"[^\d,.\-]", "", t)
    # si hay ambos ',' y '.' decide por el separador final como decimal
    if "," in t and "." in t:
        # asume formato LATAM: miles='.' decimal=','
        t = t.replace(".", "").replace(",", ".")
    else:
        # si solo hay ',', úsalo como decimal
        if "," in t and "." not in t:
            t = t.replace(",", ".")
    try:
        return Decimal(t)
    except InvalidOperation:
        return None

def _parse_date_any(s: str) -> Optional[str]:
    s = s.strip()
    # formatos más comunes: 31/12/2024, 2024-12-31, 31-12-2024, 31.12.2024
    fmts = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y", "%d %m %Y"]
    for f in fmts:
        try:
            dt = datetime.strptime(s, f).date()
            return dt.isoformat()
        except Exception:
            pass
    return None

# Validador simple de RUC peruano (módulo 11)
def _valid_ruc(ruc: str) -> bool:
    if not re.fullmatch(r"\d{11}", ruc):
        return False
    fac = [5,4,3,2,7,6,5,4,3,2]  # pesos para los 10 primeros
    s = sum(int(d)*w for d, w in zip(ruc[:10], fac))
    r = 11 - (s % 11)
    dv = 0 if r == 11 else (1 if r == 10 else r)
    return dv == int(ruc[-1])

# ------------ OCR helpers ------------

def _images_from_pdf(pdf_path: str) -> List[Image.Image]:
    return convert_from_path(pdf_path, dpi=300)

def _text_from_image(img: Image.Image) -> str:
    return pytesseract.image_to_string(img, lang="spa+eng")

# ------------ Extractores de campos ------------

def _extract_ruc(text: str) -> Optional[str]:
    # 1) preferente: “RUC ... 11 dígitos”
    m = re.search(r"(?:\bRUC\b|R\.?U\.?C\.?)\D*?(\d{11})", text, re.IGNORECASE)
    if m and _valid_ruc(m.group(1)):
        return m.group(1)
    # 2) fallback: cualquier 11 dígitos que pase checksum
    for m in re.finditer(r"\b(\d{11})\b", text):
        if _valid_ruc(m.group(1)):
            return m.group(1)
    return None

def _extract_currency(text: str) -> Optional[str]:
    # prioridad por tokens inequívocos
    if re.search(r"\bUSD\b|\bUS?\$\b|\bDOLARES?\b", text, re.IGNORECASE):
        return "USD"
    if re.search(r"\bPEN\b|\bSOLES?\b|\bS\/\.?", text, re.IGNORECASE):
        return "PEN"

    # heurística: si aparece "S/" muchas veces -> PEN; si "$" sin "US" cerca -> USD
    s_count = len(re.findall(r"S\/", text))
    dollar_count = len(re.findall(r"(?<!US)\$", text))  # ojo: \$ para el símbolo
    if s_count > 0 and dollar_count == 0:
        return "PEN"
    if dollar_count > 0:
        return "USD"
    return None

def _extract_total(text: str) -> Optional[Decimal]:
    # buscar “IMPORTE TOTAL”, “TOTAL”, “TOTAL A PAGAR”
    pats = [
        r"IMPORTE\s+TOTAL[:\s]*([S\$]*\s*[\d\.\,]+)",
        r"TOTAL\s*A\s*PAGAR[:\s]*([S\$]*\s*[\d\.\,]+)",
        r"\bTOTAL\b[:\s]*([S\$]*\s*[\d\.\,]+)"
    ]
    for p in pats:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            v = re.sub(r"[S$ ]", "", m.group(1))
            d = _to_decimal(v)
            if d is not None:
                return d
    # fallback: toma la mayor cifra tipo dinero que aparezca
    candidates = [c for c in re.findall(r"([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{2}))", text)]
    best = None
    for c in candidates:
        d = _to_decimal(c)
        if d is not None and (best is None or d > best):
            best = d
    return best

def _extract_date(text: str) -> Optional[str]:
    # vecinos de “FECHA EMISIÓN” / “F. EMISIÓN”
    pats = [
        r"FECHA\s*(?:DE\s*)?EMISI[ÓO]N[:\s]*([0-9./-]{8,10})",
        r"F\.?\s*EMISI[ÓO]N[:\s]*([0-9./-]{8,10})",
        r"\bEMISI[ÓO]N[:\s]*([0-9./-]{8,10})",
        r"\bFECHA[:\s]*([0-9./-]{8,10})"
    ]
    for p in pats:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            d = _parse_date_any(m.group(1))
            if d:
                return d
    # fallback: primera fecha con formato común
    for m in re.finditer(r"(\d{2}[./-]\d{2}[./-]\d{4}|\d{4}-\d{2}-\d{2})", text):
        d = _parse_date_any(m.group(1))
        if d:
            return d
    return None

def _extract_invoice_number(text: str) -> Optional[str]:
    # 1) Formatos con serie-tipo típicos: F001-123456, B001-654321, 001-123456
    m = re.search(r"\b([FB]\d{3}-\d{1,12})\b", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = re.search(r"\b(\d{3}-\d{1,12})\b", text)
    if m:
        return m.group(1)
    # 2) Número solo dígitos cerca de “FACTURA/BOLETA/N°/No/#”
    ctx = re.search(r"(FACTURA|BOLETA|N[°o]|#)\s*[:\-]?\s*(\d{6,12})", text, re.IGNORECASE)
    if ctx:
        return ctx.group(2)
    # 3) otra heurística: tras serie tipo F001 o B001 en ±30 chars
    m = re.search(r"\b([FB]\d{3})\b.{0,30}\b(\d{6,12})\b", text, re.IGNORECASE | re.DOTALL)
    if m:
        return f"{m.group(1).upper()}-{m.group(2)}"
    return None

# ------------ Interfaz pública ------------

def analyze_file_local(local_path: str) -> Dict[str, Any]:
    pages_text: List[str] = []
    if local_path.lower().endswith(".pdf"):
        for im in _images_from_pdf(local_path):
            pages_text.append(_text_from_image(im))
    else:
        pages_text.append(_text_from_image(Image.open(local_path)))

    full_text = "\n".join(pages_text)

    ruc = _extract_ruc(full_text)
    moneda = _extract_currency(full_text)
    total = _extract_total(full_text)
    fecha = _extract_date(full_text)
    numero = _extract_invoice_number(full_text)

    parsed = {
        "provider": {  # mantenemos nodo por compatibilidad, pero sin razón social
            "ruc": ruc
        },
        "invoice": {
            "numero": numero,
            "fecha": fecha,
            "moneda": moneda,
            "total": str(total) if total is not None else None
        },
        "items": []  # sin extracción de ítems por ahora
    }

    # proxy de “confianza” simple
    signals = sum(x is not None for x in [ruc, moneda, total, fecha, numero])
    confidence = 0.3 + 0.14 * signals  # 0.3..1.0 aprox

    return {
        "engine": "local-tesseract",
        "confidence": float(min(confidence, 0.99)),
        "raw_text": full_text[:20000],
        "parsed": parsed
    }

# ====== añadir: helpers de OCR de archivo ======
def extract_text(local_path: str) -> str:
    """Devuelve texto OCR para PDF o imagen."""
    buf = []
    if local_path.lower().endswith(".pdf"):
        for im in _images_from_pdf(local_path):
            buf.append(_text_from_image(im))
    else:
        buf.append(_text_from_image(Image.open(local_path)))
    return "\n".join(buf)

# ====== añadir: autodetección simple del tipo ======
def autodetect_kind(text: str) -> Optional[str]:
    if re.search(r"\bBOLETA\b", text, re.IGNORECASE):
        return "boleta"
    if re.search(r"\bFACTURA\b", text, re.IGNORECASE):
        return "factura"
    # por defecto None (el router asumirá factura)
    return None

# ====== añadir: número específico por tipo ======
def _extract_invoice_number_boleta(text: str) -> Optional[str]:
    # EB01-419, B001-123456, etc.
    m = re.search(r"\b([A-Z]{1}[A-Z0-9]{2}\d{2}-\d{1,12})\b", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = re.search(r"\b(B\d{3}-\d{1,12})\b", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # contexto N°, No, # + dígitos
    ctx = re.search(r"(BOLETA|N[°o]|#)\s*[:\-]?\s*(\d{6,12})", text, re.IGNORECASE)
    if ctx:
        return ctx.group(2)
    return None

def _extract_invoice_number_factura(text: str) -> Optional[str]:
    m = re.search(r"\b(F\d{3}-\d{1,12})\b", text, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    ctx = re.search(r"(FACTURA|N[°o]|#)\s*[:\-]?\s*(\d{6,12})", text, re.IGNORECASE)
    if ctx:
        return ctx.group(2)
    return None

# ====== añadir: parseadores por tipo ======
def parse_boleta_local(text: str) -> Dict[str, Any]:
    ruc = _extract_ruc(text)
    moneda = _extract_currency(text)
    total = _extract_total(text)
    fecha = _extract_date(text)
    numero = _extract_invoice_number_boleta(text)

    parsed = {
        "provider": {"ruc": ruc},
        "invoice": {
            "numero": numero,
            "fecha": fecha,
            "moneda": moneda,
            "total": str(total) if total is not None else None
        },
        "items": []
    }
    signals = sum(x is not None for x in [ruc, moneda, total, fecha, numero])
    confidence = 0.3 + 0.14 * signals
    return {"engine": "local-tesseract", "confidence": float(min(confidence, 0.99)), "parsed": parsed}

def parse_factura_local(text: str) -> Dict[str, Any]:
    ruc = _extract_ruc(text)
    moneda = _extract_currency(text)
    total = _extract_total(text)
    fecha = _extract_date(text)
    numero = _extract_invoice_number_factura(text)

    parsed = {
        "provider": {"ruc": ruc},
        "invoice": {
            "numero": numero,
            "fecha": fecha,
            "moneda": moneda,
            "total": str(total) if total is not None else None
        },
        "items": []
    }
    signals = sum(x is not None for x in [ruc, moneda, total, fecha, numero])
    confidence = 0.3 + 0.14 * signals
    return {"engine": "local-tesseract", "confidence": float(min(confidence, 0.99)), "parsed": parsed}

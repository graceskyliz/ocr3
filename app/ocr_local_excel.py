# app/ocr_local_excel.py
import pandas as pd
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any


REQ = {"fecha","moneda","total"}

def parse_excel_local(path: str) -> Dict:
    df = pd.read_excel(path)  # requiere openpyxl
    cols = {c.lower(): c for c in df.columns}
    missing = REQ - set(cols)
    if missing:
        raise ValueError(f"Excel debe contener columnas: {sorted(REQ)}. Faltan: {sorted(missing)}")

    r = df.iloc[0]  # MVP: 1 fila
    def get(name, default=None):
        col = cols.get(name)
        if col is None: return default
        val = r[col]
        return default if pd.isna(val) else val

    # fecha robusta
    raw_fecha = get("fecha")
    fecha = None
    if raw_fecha is not None:
        try:
            fecha = str(pd.to_datetime(raw_fecha).date())
        except Exception:
            fecha = None

    moneda = (str(get("moneda","")).strip().upper() or None)
    total  = str(Decimal(str(get("total","0"))))
    numero = str(get("numero")) if "numero" in cols and get("numero") is not None else None
    ruc    = str(get("ruc"))    if "ruc" in cols and get("ruc") is not None else None

    parsed = {
        "provider": {"ruc": ruc},
        "invoice": {"numero": numero, "fecha": fecha, "moneda": moneda, "total": total},
        "items": []
    }
    return {"engine":"local-excel","confidence":0.99,"parsed":parsed}

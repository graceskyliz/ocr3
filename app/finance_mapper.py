# app/finance_mapper.py
import uuid
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from .finance_models import Provider, Invoice, InvoiceItem

def _to_decimal(x):
    if x is None or x == "":
        return None
    try:
        return Decimal(str(x))
    except InvalidOperation:
        return None

def _to_date(x):
    if not x:
        return None
    if isinstance(x, (date, datetime)):
        return x.date() if isinstance(x, datetime) else x
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(str(x), fmt).date()
        except Exception:
            pass
    return None

def _get_doc_row(db: Session, doc_id: str):
    row = db.execute(
        text("""
            SELECT id::text AS id, tenant_id::text AS tenant_id, storage_key, filename, mime
            FROM documents.documents
            WHERE id = :id
        """),
        {"id": doc_id}
    ).fetchone()
    if not row:
        raise ValueError(f"document {doc_id} no existe")
    return dict(row._mapping)

def _get_or_create_provider(db: Session, tenant_id: str, ruc: str | None, razon: str | None):
    # Busca por RUC dentro del tenant. Si no hay RUC, crea uno “anónimo”.
    prov = None
    if ruc:
        prov = db.query(Provider).filter(
            Provider.tenant_id == uuid.UUID(tenant_id),
            Provider.ruc == ruc
        ).one_or_none()
    if not prov:
        prov = Provider(
            id = uuid.uuid4(),
            tenant_id = uuid.UUID(tenant_id),
            ruc = ruc,
            razon_social = razon,
            estado = "activo",
            meta = {}
        )
        db.add(prov)
        db.flush()
    return prov

def materialize_invoice(db: Session, doc_id: str, engine: str, result: dict):
    """
    Persistir provider + invoice + items a partir del resultado de OCR.
    - doc_id: UUID del documento (documents.documents.id)
    - engine: "local-tesseract" | "textract-analyze-expense"
    - result: dict con claves como:
        {
          "engine": "...",
          "confidence": 0.87,
          "parsed": {
            "provider": {"ruc": "...", "razon_social": "..."},
            "invoice":  {"fecha": "2025-11-11", "moneda": "PEN", "total": "123.45"},
            "items":    [ ... ]
          }
        }
    """
    doc = _get_doc_row(db, doc_id)                     # ← obtenemos tenant_id del documento
    tenant_id = doc["tenant_id"]
    doc_uuid = uuid.UUID(doc["id"])

    parsed = (result or {}).get("parsed") or {}
    prov_in = (parsed.get("provider") or {})
    inv_in  = (parsed.get("invoice")  or {})
    items_in = (parsed.get("items")   or [])

    provider = _get_or_create_provider(
        db=db,
        tenant_id=tenant_id,
        ruc=prov_in.get("ruc"),
        razon=prov_in.get("razon_social")
    )

    inv = Invoice(
        id = uuid.uuid4(),
        tenant_id = uuid.UUID(tenant_id),
        provider_id = provider.id,
        document_id = doc_uuid,                         # ← FIX: usar el doc_id real
        serie = inv_in.get("serie"),
        numero = inv_in.get("numero"),
        fecha = _to_date(inv_in.get("fecha")),
        moneda = inv_in.get("moneda"),
        subtotal = _to_decimal(inv_in.get("subtotal")),
        igv = _to_decimal(inv_in.get("igv")),
        total = _to_decimal(inv_in.get("total")),
        status = "registrada",
        due_date = _to_date(inv_in.get("due_date")),
        meta = {"engine": engine, "confidence": result.get("confidence")}
    )
    db.add(inv)
    db.flush()

    for it in items_in:
        item = InvoiceItem(
            id = uuid.uuid4(),
            invoice_id = inv.id,
            descripcion = (it.get("descripcion") or it.get("desc")),
            cantidad = _to_decimal(it.get("cantidad") or it.get("qty")),
            precio_unit = _to_decimal(it.get("precio_unit") or it.get("unit_price")),
            igv = _to_decimal(it.get("igv")),
            total = _to_decimal(it.get("total")),
            category_id = None
        )
        db.add(item)

    db.commit()
    return inv.id

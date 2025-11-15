# app/finance_mapper.py
import uuid
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from .finance_models import Provider, Invoice, InvoiceItem
from typing import Optional


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
            SELECT id::text AS id, tenant_id, storage_key, filename, mime
            FROM documents.documents
            WHERE id = :id
        """),
        {"id": doc_id}
    ).fetchone()
    if not row:
        raise ValueError(f"document {doc_id} no existe")
    return dict(row._mapping)

def _get_or_create_provider(db: Session, tenant_id: str, ruc: Optional[str]):
    prov = None
    if ruc:
        prov = db.query(Provider).filter(
            Provider.tenant_id == tenant_id,
            Provider.ruc == ruc
        ).one_or_none()
    if not prov:
        prov = Provider(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            ruc=ruc,
            razon_social=None,  # ya no usamos razón social
            estado="activo",
            meta={}
        )
        db.add(prov)
        db.flush()
    return prov

def materialize_invoice(db: Session, doc_id: str, engine: str, result: dict):
    doc = _get_doc_row(db, doc_id)
    tenant_id = doc["tenant_id"]
    doc_uuid = uuid.UUID(doc["id"])

    parsed = (result or {}).get("parsed") or {}
    prov_in = (parsed.get("provider") or {})
    inv_in  = (parsed.get("invoice") or {})

    provider = _get_or_create_provider(db, tenant_id, prov_in.get("ruc"))

    inv = Invoice(
        id = uuid.uuid4(),
        tenant_id = tenant_id,
        provider_id = provider.id,
        document_id = doc_uuid,
        serie = None,  # no lo usamos por ahora
        numero = inv_in.get("numero"),
        fecha = _to_date(inv_in.get("fecha")),
        moneda = inv_in.get("moneda"),
        subtotal = None,
        igv = None,
        total = _to_decimal(inv_in.get("total")),
        status = "registrada",
        due_date = None,
        meta = {"engine": engine, "confidence": result.get("confidence")}
    )
    db.add(inv)
    db.flush()

    db.commit()
    return inv.id
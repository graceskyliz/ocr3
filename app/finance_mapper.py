from datetime import datetime
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from .finance_models import Provider, Invoice, InvoiceItem
import uuid

def _to_decimal(x):
    try:
        return Decimal(str(x).replace(",", "").strip())
    except Exception:
        return None

def _to_date(x):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try: return datetime.strptime(x.strip(), fmt).date()
        except Exception: pass
    return None

def _norm_label(fields: dict, *names):
    for n in names:
        v = fields.get(n)
        if v: return v
    return None

def materialize_invoice(db: Session, tenant_id: uuid.UUID, document_id: uuid.UUID, result: dict):
    f = { (k.lower() if k else k): (v or "") for k,v in (result.get("fields") or {}).items() }

    ruc          = _norm_label(f, "ruc", "supplier tax id", "tax id", "ruc del proveedor")
    proveedor    = _norm_label(f, "proveedor", "supplier", "vendor name", "razón social", "razon social")
    fecha        = _to_date(_norm_label(f, "fecha", "date", "issue date") or "")
    serie        = _norm_label(f, "serie", "series")
    numero       = _norm_label(f, "numero", "number", "invoice number")
    moneda       = _norm_label(f, "moneda", "currency")
    subtotal     = _to_decimal(_norm_label(f, "subtotal", "net", "sub total"))
    igv          = _to_decimal(_norm_label(f, "igv", "tax", "vat"))
    total        = _to_decimal(_norm_label(f, "total", "amount due", "grand total"))

    # upsert de proveedor por (tenant_id, ruc) o por nombre
    provider = None
    if ruc:
        provider = db.scalar(select(Provider).where(Provider.tenant_id==tenant_id, Provider.ruc==ruc))
    if not provider and proveedor:
        provider = db.scalar(select(Provider).where(Provider.tenant_id==tenant_id, Provider.razon_social==proveedor))

    if not provider:
        provider = Provider(id=uuid.uuid4(), tenant_id=tenant_id, ruc=ruc, razon_social=proveedor, estado="activo")
        db.add(provider)
        db.flush()

    inv = Invoice(
        id=uuid.uuid4(), tenant_id=tenant_id, provider_id=provider.id, document_id=document_id,
        serie=serie, numero=numero, fecha=fecha, moneda=moneda,
        subtotal=subtotal, igv=igv, total=total, status="registrada", meta=f
    )
    db.add(inv)
    db.flush()

    # Items (si hay)
    for row in (result.get("items") or []):
        desc = row.get("description") or row.get("descripcion") or row.get("item") or ""
        cantidad = _to_decimal(row.get("cantidad") or row.get("quantity") or "")
        pu = _to_decimal(row.get("precio unitario") or row.get("unit price") or row.get("precio_unit") or "")
        igv_i = _to_decimal(row.get("igv") or row.get("tax") or "")
        total_i = _to_decimal(row.get("total") or "")
        db.add(InvoiceItem(
            id=uuid.uuid4(), invoice_id=inv.id, descripcion=desc,
            cantidad=cantidad, precio_unit=pu, igv=igv_i, total=total_i
        ))
    return inv.id

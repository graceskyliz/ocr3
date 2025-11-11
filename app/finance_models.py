from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import String, Text, Numeric, Date, ForeignKey
import uuid
from .models import Base

class Provider(Base):
    __tablename__ = "providers"
    __table_args__ = {"schema": "finance"}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    ruc: Mapped[str | None] = mapped_column(String(16))
    razon_social: Mapped[str | None] = mapped_column(Text)
    direccion: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str | None] = mapped_column(String(32))
    metadata: Mapped[dict | None] = mapped_column(JSONB)

class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = {"schema": "finance"}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    provider_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("finance.providers.id"))
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.documents.id"))
    serie: Mapped[str | None] = mapped_column(String(32))
    numero: Mapped[str | None] = mapped_column(String(64))
    fecha: Mapped[Date | None] = mapped_column(Date)
    moneda: Mapped[str | None] = mapped_column(String(8))
    subtotal: Mapped[Numeric | None] = mapped_column(Numeric)
    igv: Mapped[Numeric | None] = mapped_column(Numeric)
    total: Mapped[Numeric | None] = mapped_column(Numeric)
    status: Mapped[str | None] = mapped_column(String(32))
    due_date: Mapped[Date | None] = mapped_column(Date)
    meta: Mapped[dict | None] = mapped_column(JSONB)

class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    __table_args__ = {"schema": "finance"}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("finance.invoices.id"))
    descripcion: Mapped[str | None] = mapped_column(Text)
    cantidad: Mapped[Numeric | None] = mapped_column(Numeric)
    precio_unit: Mapped[Numeric | None] = mapped_column(Numeric)
    igv: Mapped[Numeric | None] = mapped_column(Numeric)
    total: Mapped[Numeric | None] = mapped_column(Numeric)
    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

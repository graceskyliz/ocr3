from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy import Column, String, Text, Numeric, Date, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Provider(Base):
    __tablename__ = "providers"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    ruc = Column(String(16))
    razon_social = Column(Text)
    direccion = Column(Text)
    estado = Column(Text)
    # atributo Python 'meta', columna física 'metadata'
    meta = Column("metadata", JSONB)

    invoices = relationship("Invoice", back_populates="provider", lazy="selectin")


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(Text, nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("finance.providers.id"))
    document_id = Column(UUID(as_uuid=True))  # o FK a documents.documents si lo definiste
    serie = Column(Text)
    numero = Column(Text)
    fecha = Column(Date)
    moneda = Column(Text)
    subtotal = Column(Numeric)
    igv = Column(Numeric)
    total = Column(Numeric)
    status = Column(Text)
    due_date = Column(Date)
    meta = Column(JSONB)

    provider = relationship("Provider", back_populates="invoices", lazy="joined")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    __table_args__ = {"schema": "finance"}

    id = Column(UUID(as_uuid=True), primary_key=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("finance.invoices.id"))
    descripcion = Column(Text)
    cantidad = Column(Numeric)
    precio_unit = Column(Numeric)
    igv = Column(Numeric)
    total = Column(Numeric)
    category_id = Column(UUID(as_uuid=True))

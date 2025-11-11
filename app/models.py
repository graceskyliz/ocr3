from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, DOUBLE_PRECISION
import uuid

class Base(DeclarativeBase): pass

class Document(Base):
    __tablename__ = "documents"
    __table_args__ = {"schema": "documents"}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    filename: Mapped[str] = mapped_column(Text)
    storage_key: Mapped[str] = mapped_column(Text)
    mime: Mapped[str] = mapped_column(String(128))
    size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="uploaded")

class Extraction(Base):
    __tablename__ = "extractions"
    __table_args__ = {"schema": "extractor"}
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.documents.id"))
    engine: Mapped[str] = mapped_column(String(64))
    json: Mapped[dict] = mapped_column(JSONB)
    confidence: Mapped[float | None] = mapped_column(DOUBLE_PRECISION)
    status: Mapped[str] = mapped_column(String(16), default="ok")
    error_message: Mapped[str | None] = mapped_column(Text)

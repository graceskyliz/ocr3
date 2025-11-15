# app/auth_models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
import uuid
from datetime import datetime

from .models import Base


class Tenant(Base):
    """Modelo de Tenant/Empresa - cada tenant representa una empresa u organización"""
    __tablename__ = "tenants"
    __table_args__ = {"schema": "auth"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    whatsapp_number: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True, index=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan: Mapped[str] = mapped_column(String(32), default="free")
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class User(Base):
    """Modelo de Usuario - pertenece a un tenant"""
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("auth.tenants.id"), nullable=False)
    
    # Campos opcionales según método de registro
    email: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Información adicional
    source: Mapped[str] = mapped_column(String(32), default="whatsapp")  # whatsapp, web, api
    role: Mapped[str] = mapped_column(String(32), default="owner")  # owner, admin, user
    onboarding_step: Mapped[str] = mapped_column(String(32), default="complete")
    
    # Metadata
    provider: Mapped[str | None] = mapped_column(Text, nullable=True)
    ruc: Mapped[str | None] = mapped_column(String(16), nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)

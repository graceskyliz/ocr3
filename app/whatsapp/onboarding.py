# app/whatsapp/onboarding.py
"""Lógica de auto-onboarding de usuarios vía WhatsApp"""
import logging
import uuid
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..auth_models import Tenant, User

log = logging.getLogger(__name__)


def get_or_create_tenant_by_whatsapp(
    db: Session, 
    whatsapp_number: str
) -> Tuple[Tenant, User, bool]:
    """
    Obtiene o crea un tenant y usuario basado en el número de WhatsApp.
    
    Args:
        db: Sesión de base de datos
        whatsapp_number: Número de WhatsApp en formato internacional
    
    Returns:
        Tupla (Tenant, User, is_new) donde is_new indica si se creó un nuevo tenant
    """
    # Buscar tenant existente por whatsapp_number
    stmt = select(Tenant).where(Tenant.whatsapp_number == whatsapp_number)
    tenant = db.execute(stmt).scalar_one_or_none()
    
    if tenant:
        # Tenant existe, buscar usuario asociado
        user_stmt = select(User).where(User.tenant_id == tenant.id).limit(1)
        user = db.execute(user_stmt).scalar_one_or_none()
        
        if not user:
            # Crear usuario si no existe (caso edge)
            user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                phone=whatsapp_number,
                source="whatsapp",
                role="owner",
                onboarding_step="complete"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            log.info(f"Usuario creado para tenant existente: {user.id}")
        
        log.info(f"Tenant existente encontrado: {tenant.id}")
        return tenant, user, False
    
    # Crear nuevo tenant
    log.info(f"Creando nuevo tenant para WhatsApp: {whatsapp_number}")
    tenant = Tenant(
        id=uuid.uuid4(),
        whatsapp_number=whatsapp_number,
        name=f"WhatsApp User {whatsapp_number[-4:]}",
        plan="free",
        status="active"
    )
    db.add(tenant)
    db.flush()  # Para obtener el tenant.id
    
    # Crear usuario owner
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        phone=whatsapp_number,
        source="whatsapp",
        role="owner",
        onboarding_step="complete"
    )
    db.add(user)
    
    db.commit()
    db.refresh(tenant)
    db.refresh(user)
    
    log.info(f"Nuevo tenant y usuario creados: tenant_id={tenant.id}, user_id={user.id}")
    return tenant, user, True


def get_tenant_by_whatsapp(db: Session, whatsapp_number: str) -> Optional[Tenant]:
    """
    Busca un tenant por número de WhatsApp.
    
    Args:
        db: Sesión de base de datos
        whatsapp_number: Número de WhatsApp
    
    Returns:
        Tenant si existe, None si no
    """
    stmt = select(Tenant).where(Tenant.whatsapp_number == whatsapp_number)
    return db.execute(stmt).scalar_one_or_none()

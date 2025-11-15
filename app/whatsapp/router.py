# app/whatsapp/router.py
"""Router principal para webhook de WhatsApp con auto-onboarding"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request, Query, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from .onboarding import get_or_create_tenant_by_whatsapp
from .processor import process_whatsapp_media, format_ocr_response
from .client import send_whatsapp_message
from .helpers import (
    get_welcome_message,
    get_instructions_message,
    get_processing_message,
    get_unsupported_format_message,
    sanitize_phone_number
)

router = APIRouter(prefix="/webhook", tags=["whatsapp"])
log = logging.getLogger(__name__)

# Token de verificación desde variables de entorno
import os
APP_VERIFY_TOKEN = os.getenv("APP_VERIFY_TOKEN", "thesaurus-whatsapp")


@router.get("/whatsapp")
async def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge")
):
    """
    Endpoint de verificación de webhook para Meta/WhatsApp.
    
    Meta envía estos parámetros para verificar que el webhook es legítimo:
    - hub.mode: debe ser "subscribe"
    - hub.verify_token: debe coincidir con APP_VERIFY_TOKEN
    - hub.challenge: valor que debemos devolver si la verificación es exitosa
    """
    log.info(f"Verificación de webhook: mode={mode}, token={token}")
    
    if mode == "subscribe" and token == APP_VERIFY_TOKEN:
        log.info("✅ Webhook verificado exitosamente")
        return int(challenge)
    
    log.warning("❌ Verificación fallida: token incorrecto o mode inválido")
    raise HTTPException(status_code=403, detail="Verificación de webhook fallida")


@router.post("/whatsapp")
async def handle_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint que recibe notificaciones de WhatsApp cuando llegan mensajes.
    
    Implementa auto-onboarding completo:
    1. Detecta número de WhatsApp del remitente
    2. Busca o crea tenant/usuario automáticamente
    3. Procesa mensajes de texto, imágenes y documentos
    4. Guarda en BD (documents, extractions)
    5. Responde con resultados formateados
    """
    try:
        body = await request.json()
        log.info(f"Webhook recibido: {body}")
        
        # Verificar estructura del payload
        if body.get("object") != "whatsapp_business_account":
            log.warning("Payload no es de WhatsApp Business")
            return {"status": "ignored"}
        
        # Extraer información del mensaje
        entries = body.get("entry", [])
        
        for entry in entries:
            changes = entry.get("changes", [])
            
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                
                for message in messages:
                    from_number = message.get("from")
                    message_type = message.get("type")
                    message_id = message.get("id")
                    
                    if not from_number:
                        log.warning("Mensaje sin número de origen")
                        continue
                    
                    # Sanitizar número
                    from_number = sanitize_phone_number(from_number)
                    
                    log.info(f"Mensaje de {from_number}, tipo: {message_type}")
                    
                    # ========================================
                    # AUTO-ONBOARDING
                    # ========================================
                    tenant, user, is_new = get_or_create_tenant_by_whatsapp(db, from_number)
                    
                    log.info(f"Tenant: {tenant.id}, Usuario: {user.id}, Nuevo: {is_new}")
                    
                    # Si es nuevo, enviar mensaje de bienvenida
                    if is_new:
                        await send_whatsapp_message(from_number, get_welcome_message())
                        log.info(f"Usuario nuevo registrado: {from_number}")
                    
                    # ========================================
                    # PROCESAR SEGÚN TIPO DE MENSAJE
                    # ========================================
                    
                    if message_type == "text":
                        # Mensaje de texto simple
                        text_body = message.get("text", {}).get("body", "").lower()
                        log.info(f"Texto recibido: {text_body}")
                        
                        # Comandos especiales
                        if text_body in ["ayuda", "help", "?", "instrucciones"]:
                            await send_whatsapp_message(from_number, get_instructions_message())
                        elif text_body in ["hola", "hi", "hello", "ola"]:
                            greeting = "👋 ¡Hola de nuevo!\n\n" + get_instructions_message()
                            await send_whatsapp_message(from_number, greeting)
                        else:
                            # Responder con instrucciones generales
                            await send_whatsapp_message(from_number, get_instructions_message())
                    
                    elif message_type == "image":
                        # Imagen recibida
                        image = message.get("image", {})
                        media_id = image.get("id")
                        mime_type = image.get("mime_type", "image/jpeg")
                        filename = image.get("filename", f"image_{message_id}.jpg")
                        
                        if not media_id:
                            log.warning("Imagen sin media_id")
                            continue
                        
                        # Enviar mensaje de procesamiento
                        await send_whatsapp_message(from_number, get_processing_message())
                        
                        # Procesar imagen con OCR y guardar en BD
                        result = await process_whatsapp_media(
                            db=db,
                            tenant_id=str(tenant.id),
                            user_id=str(user.id),
                            media_id=media_id,
                            mime_type=mime_type,
                            filename=filename,
                            from_number=from_number
                        )
                        
                        # Formatear y enviar resultado
                        response_text = format_ocr_response(result)
                        await send_whatsapp_message(from_number, response_text)
                    
                    elif message_type == "document":
                        # Documento (PDF) recibido
                        document = message.get("document", {})
                        media_id = document.get("id")
                        mime_type = document.get("mime_type", "application/pdf")
                        filename = document.get("filename", f"document_{message_id}.pdf")
                        
                        if not media_id:
                            log.warning("Documento sin media_id")
                            continue
                        
                        # Enviar mensaje de procesamiento
                        await send_whatsapp_message(from_number, get_processing_message())
                        
                        # Procesar documento con OCR y guardar en BD
                        result = await process_whatsapp_media(
                            db=db,
                            tenant_id=str(tenant.id),
                            user_id=str(user.id),
                            media_id=media_id,
                            mime_type=mime_type,
                            filename=filename,
                            from_number=from_number
                        )
                        
                        # Formatear y enviar resultado
                        response_text = format_ocr_response(result)
                        await send_whatsapp_message(from_number, response_text)
                    
                    else:
                        # Tipo de mensaje no soportado
                        log.warning(f"Tipo de mensaje no soportado: {message_type}")
                        await send_whatsapp_message(from_number, get_unsupported_format_message())
        
        return {"status": "ok"}
        
    except Exception as e:
        log.error(f"Error procesando webhook: {e}", exc_info=True)
        # No lanzar error para no bloquear el webhook de Meta
        return {"status": "error", "message": str(e)}

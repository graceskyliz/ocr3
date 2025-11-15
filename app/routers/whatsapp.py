# app/routers/whatsapp.py
import os
import logging
from typing import Dict, Any, Optional
import httpx
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel

from ..settings import settings
from ..storage_local import save_file_local
from ..gemini_client import analyze_document_gemini, analyze_pdf_with_gemini

router = APIRouter(prefix="/webhook", tags=["whatsapp"])
log = logging.getLogger(__name__)

# Configuración de WhatsApp desde .env
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
APP_VERIFY_TOKEN = os.getenv("APP_VERIFY_TOKEN", "thesaurus-whatsapp")

# Validar que las variables estén configuradas
if not WHATSAPP_TOKEN:
    log.warning("WHATSAPP_TOKEN no está configurado en .env")
if not PHONE_NUMBER_ID:
    log.warning("PHONE_NUMBER_ID no está configurado en .env")


class WhatsAppMessage(BaseModel):
    """Modelo simplificado del payload de WhatsApp"""
    object: str
    entry: list


async def send_whatsapp_message(to: str, text: str) -> Dict[str, Any]:
    """
    Envía un mensaje de texto por WhatsApp.
    
    Args:
        to: Número de teléfono del destinatario (formato internacional sin +)
        text: Texto del mensaje a enviar
    
    Returns:
        Respuesta de la API de WhatsApp
    """
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        raise HTTPException(status_code=500, detail="WhatsApp no está configurado")
    
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()
            log.info(f"Mensaje enviado a {to}")
            return response.json()
    except httpx.HTTPError as e:
        log.error(f"Error enviando mensaje a WhatsApp: {e}")
        raise HTTPException(status_code=502, detail=f"Error al enviar mensaje: {str(e)}")


async def download_media(media_id: str) -> bytes:
    """
    Descarga un archivo multimedia de WhatsApp.
    
    Args:
        media_id: ID del archivo multimedia en WhatsApp
    
    Returns:
        Contenido del archivo en bytes
    """
    if not WHATSAPP_TOKEN:
        raise HTTPException(status_code=500, detail="WHATSAPP_TOKEN no configurado")
    
    # Paso 1: Obtener URL de descarga
    url_info = f"https://graph.facebook.com/v17.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    
    try:
        async with httpx.AsyncClient() as client:
            # Obtener información del archivo
            response = await client.get(url_info, headers=headers, timeout=10.0)
            response.raise_for_status()
            media_info = response.json()
            download_url = media_info.get("url")
            
            if not download_url:
                raise HTTPException(status_code=422, detail="No se pudo obtener URL de descarga")
            
            # Paso 2: Descargar el archivo
            log.info(f"Descargando media desde: {download_url}")
            download_response = await client.get(download_url, headers=headers, timeout=30.0)
            download_response.raise_for_status()
            
            return download_response.content
            
    except httpx.HTTPError as e:
        log.error(f"Error descargando media {media_id}: {e}")
        raise HTTPException(status_code=502, detail=f"Error al descargar archivo: {str(e)}")


async def process_whatsapp_media(media_id: str, mime_type: str, filename: str, from_number: str) -> str:
    """
    Procesa un archivo multimedia recibido por WhatsApp.
    
    Args:
        media_id: ID del archivo en WhatsApp
        mime_type: Tipo MIME del archivo
        filename: Nombre del archivo
        from_number: Número del remitente
    
    Returns:
        Texto con los resultados del OCR
    """
    try:
        # 1. Descargar archivo
        log.info(f"Procesando media {media_id} de {from_number}")
        file_content = await download_media(media_id)
        
        # 2. Guardar archivo localmente
        import io
        tenant_id = "whatsapp"  # Puedes usar el número o un tenant específico
        doc_id = media_id  # Usar media_id como identificador
        
        storage_key = save_file_local(
            io.BytesIO(file_content), 
            tenant_id, 
            doc_id, 
            filename
        )
        
        # 3. Obtener ruta completa del archivo
        from ..storage_local import get_file_path
        file_path = get_file_path(storage_key)
        
        # 4. Procesar con OCR según tipo de archivo
        if mime_type == "application/pdf" or filename.lower().endswith(".pdf"):
            ocr_result = analyze_pdf_with_gemini(file_path, doc_kind="factura")
        elif mime_type in ["image/jpeg", "image/png"] or filename.lower().endswith((".jpg", ".jpeg", ".png")):
            ocr_result = analyze_document_gemini(file_path, doc_kind="factura")
        else:
            return f"⚠️ Formato no soportado: {mime_type}\n\nPor favor envía un PDF o imagen (JPG/PNG)."
        
        # 5. Formatear respuesta
        data = ocr_result.get("parsed", {})
        provider = data.get("provider", {})
        invoice = data.get("invoice", {})
        items = data.get("items", [])
        
        response_text = "✅ *Documento procesado exitosamente*\n\n"
        response_text += f"📄 *Tipo:* {ocr_result.get('engine', 'OCR')}\n"
        response_text += f"📊 *Confianza:* {int(ocr_result.get('confidence', 0) * 100)}%\n\n"
        
        if provider.get("ruc"):
            response_text += f"🏢 *Proveedor*\n"
            response_text += f"RUC: {provider.get('ruc')}\n"
            if provider.get("razon_social"):
                response_text += f"Razón Social: {provider.get('razon_social')}\n"
            response_text += "\n"
        
        if invoice:
            response_text += f"📋 *Documento*\n"
            if invoice.get("numero"):
                response_text += f"Número: {invoice.get('numero')}\n"
            if invoice.get("fecha"):
                response_text += f"Fecha: {invoice.get('fecha')}\n"
            if invoice.get("moneda") and invoice.get("total"):
                response_text += f"Total: {invoice.get('moneda')} {invoice.get('total')}\n"
            response_text += "\n"
        
        if items:
            response_text += f"📦 *Items ({len(items)}):*\n"
            for i, item in enumerate(items[:5], 1):  # Mostrar máximo 5 items
                response_text += f"{i}. {item.get('descripcion', 'N/A')} - {item.get('total', 'N/A')}\n"
            if len(items) > 5:
                response_text += f"... y {len(items) - 5} items más\n"
        
        return response_text
        
    except Exception as e:
        log.error(f"Error procesando media: {e}")
        return f"❌ Error al procesar el documento:\n{str(e)}\n\nPor favor intenta nuevamente."


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
    
    log.warning(f"❌ Verificación fallida: token incorrecto o mode inválido")
    raise HTTPException(status_code=403, detail="Verificación de webhook fallida")


@router.post("/whatsapp")
async def handle_webhook(request: Request):
    """
    Endpoint que recibe notificaciones de WhatsApp cuando llegan mensajes.
    
    Procesa mensajes de texto, imágenes y documentos.
    Para imágenes y PDFs, descarga el archivo, lo procesa con OCR
    y responde al usuario con los resultados.
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
                    
                    log.info(f"Mensaje de {from_number}, tipo: {message_type}")
                    
                    # Procesar según tipo de mensaje
                    if message_type == "text":
                        # Mensaje de texto simple
                        text_body = message.get("text", {}).get("body", "")
                        log.info(f"Texto recibido: {text_body}")
                        
                        # Responder con instrucciones
                        await send_whatsapp_message(
                            from_number,
                            "👋 ¡Hola! Envíame una foto o PDF de tu boleta o factura y te ayudaré a extraer la información."
                        )
                    
                    elif message_type == "image":
                        # Imagen recibida
                        image = message.get("image", {})
                        media_id = image.get("id")
                        mime_type = image.get("mime_type", "image/jpeg")
                        filename = image.get("filename", f"image_{message_id}.jpg")
                        
                        if media_id:
                            # Enviar mensaje de procesamiento
                            await send_whatsapp_message(
                                from_number,
                                "⏳ Procesando tu imagen con OCR... Un momento por favor."
                            )
                            
                            # Procesar imagen
                            result_text = await process_whatsapp_media(
                                media_id, mime_type, filename, from_number
                            )
                            
                            # Enviar resultado
                            await send_whatsapp_message(from_number, result_text)
                    
                    elif message_type == "document":
                        # Documento (PDF) recibido
                        document = message.get("document", {})
                        media_id = document.get("id")
                        mime_type = document.get("mime_type", "application/pdf")
                        filename = document.get("filename", f"document_{message_id}.pdf")
                        
                        if media_id:
                            # Enviar mensaje de procesamiento
                            await send_whatsapp_message(
                                from_number,
                                "⏳ Procesando tu documento con OCR... Un momento por favor."
                            )
                            
                            # Procesar documento
                            result_text = await process_whatsapp_media(
                                media_id, mime_type, filename, from_number
                            )
                            
                            # Enviar resultado
                            await send_whatsapp_message(from_number, result_text)
                    
                    else:
                        # Tipo de mensaje no soportado
                        log.warning(f"Tipo de mensaje no soportado: {message_type}")
                        await send_whatsapp_message(
                            from_number,
                            "⚠️ Este tipo de mensaje no es soportado.\n\nPor favor envía:\n- 📸 Una imagen\n- 📄 Un archivo PDF"
                        )
        
        return {"status": "ok"}
        
    except Exception as e:
        log.error(f"Error procesando webhook: {e}", exc_info=True)
        # No lanzar error para no bloquear el webhook de Meta
        return {"status": "error", "message": str(e)}

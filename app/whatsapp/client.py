# app/whatsapp/client.py
"""Cliente para interactuar con WhatsApp Cloud API"""
import os
import logging
from typing import Dict, Any
import httpx
from fastapi import HTTPException

log = logging.getLogger(__name__)

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")


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

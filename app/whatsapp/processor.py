# app/whatsapp/processor.py
"""Procesamiento de documentos recibidos por WhatsApp"""
import logging
import uuid
import hashlib
import io
from typing import Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from ..models import Document, Extraction
from ..storage_local import save_file_local, get_file_path
from ..gemini_client import analyze_document_gemini, analyze_pdf_with_gemini
from ..finance_mapper import materialize_invoice
from .client import download_media

log = logging.getLogger(__name__)


async def process_whatsapp_media(
    db: Session,
    tenant_id: str,
    user_id: str,
    media_id: str,
    mime_type: str,
    filename: str,
    from_number: str
) -> Dict[str, Any]:
    """
    Procesa un archivo multimedia recibido por WhatsApp.
    
    Flujo completo:
    1. Descarga el archivo de WhatsApp
    2. Calcula hash SHA256
    3. Guarda en storage local
    4. Crea registro en documents.documents
    5. Procesa con OCR (Gemini)
    6. Guarda extracción en extractor.extractions
    7. Mapea a finance si es posible
    8. Retorna resultado formateado
    
    Args:
        db: Sesión de base de datos
        tenant_id: ID del tenant
        user_id: ID del usuario
        media_id: ID del archivo en WhatsApp
        mime_type: Tipo MIME del archivo
        filename: Nombre del archivo
        from_number: Número del remitente
    
    Returns:
        Dict con resultado del OCR y metadata
    """
    try:
        # 1. Descargar archivo de WhatsApp
        log.info(f"Procesando media {media_id} de {from_number}")
        file_content = await download_media(media_id)
        
        # 2. Calcular hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # 3. Crear documento en BD
        doc_id = uuid.uuid4()
        storage_key = save_file_local(
            io.BytesIO(file_content),
            tenant_id,
            str(doc_id),
            filename
        )
        
        document = Document(
            id=doc_id,
            tenant_id=tenant_id,
            user_id=user_id,
            filename=filename,
            storage_key=storage_key,
            mime=mime_type,
            size=len(file_content),
            sha256=file_hash,
            status="uploaded"
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        log.info(f"Documento guardado: {document.id}")
        
        # 4. Procesar con OCR
        file_path = get_file_path(storage_key)
        
        if mime_type == "application/pdf" or filename.lower().endswith(".pdf"):
            ocr_result = analyze_pdf_with_gemini(file_path, doc_kind="factura")
        elif mime_type in ["image/jpeg", "image/png"] or filename.lower().endswith((".jpg", ".jpeg", ".png")):
            ocr_result = analyze_document_gemini(file_path, doc_kind="factura")
        else:
            return {
                "success": False,
                "error": f"Formato no soportado: {mime_type}",
                "document_id": str(document.id)
            }
        
        # 5. Guardar extracción
        extraction = Extraction(
            id=uuid.uuid4(),
            document_id=document.id,
            engine=ocr_result.get("engine", "gemini"),
            json=ocr_result,
            confidence=ocr_result.get("confidence", 0.0),
            status="ok"
        )
        db.add(extraction)
        
        # 6. Actualizar estado del documento
        document.status = "processed"
        
        db.commit()
        db.refresh(extraction)
        
        log.info(f"Extracción guardada: {extraction.id}")
        
        # 7. Mapear a finance si es posible
        try:
            materialize_invoice(db, str(document.id), ocr_result.get("engine", "gemini"), ocr_result)
            log.info(f"Datos mapeados a finance para documento {document.id}")
        except Exception as e:
            log.warning(f"No se pudo mapear a finance: {e}")
        
        # 8. Retornar resultado
        return {
            "success": True,
            "document_id": str(document.id),
            "extraction_id": str(extraction.id),
            "ocr_result": ocr_result,
            "confidence": ocr_result.get("confidence", 0.0)
        }
        
    except Exception as e:
        log.error(f"Error procesando media: {e}", exc_info=True)
        
        # Marcar documento como fallido si fue creado
        if 'document' in locals():
            document.status = "failed"
            db.commit()
        
        return {
            "success": False,
            "error": str(e),
            "document_id": str(document.id) if 'document' in locals() else None
        }


def format_ocr_response(result: Dict[str, Any]) -> str:
    """
    Formatea el resultado del OCR para enviar por WhatsApp.
    
    Args:
        result: Resultado del procesamiento
    
    Returns:
        Mensaje formateado en Markdown compatible con WhatsApp
    """
    if not result.get("success"):
        error = result.get("error", "Error desconocido")
        return f"❌ *Error al procesar el documento*\n\n{error}\n\nPor favor intenta nuevamente."
    
    ocr_result = result.get("ocr_result", {})
    data = ocr_result.get("parsed", {})
    provider = data.get("provider", {})
    invoice = data.get("invoice", {})
    items = data.get("items", [])
    
    response_text = "✅ *Documento procesado exitosamente*\n\n"
    response_text += f"📄 *Motor:* {ocr_result.get('engine', 'OCR')}\n"
    response_text += f"📊 *Confianza:* {int(result.get('confidence', 0) * 100)}%\n\n"
    
    if provider.get("ruc"):
        response_text += f"💼 *Proveedor*\n"
        response_text += f"RUC: {provider.get('ruc')}\n"
        if provider.get("razon_social"):
            response_text += f"Razón Social: {provider.get('razon_social')}\n"
        if provider.get("direccion"):
            response_text += f"Dirección: {provider.get('direccion')}\n"
        response_text += "\n"
    
    if invoice:
        response_text += f"📋 *Documento*\n"
        if invoice.get("serie"):
            response_text += f"Serie: {invoice.get('serie')}\n"
        if invoice.get("numero"):
            response_text += f"Número: {invoice.get('numero')}\n"
        if invoice.get("fecha"):
            response_text += f"Fecha: {invoice.get('fecha')}\n"
        if invoice.get("moneda") and invoice.get("total"):
            response_text += f"*Total: {invoice.get('moneda')} {invoice.get('total')}*\n"
        response_text += "\n"
    
    if items:
        response_text += f"📦 *Items ({len(items)}):*\n"
        for i, item in enumerate(items[:5], 1):  # Mostrar máximo 5 items
            desc = item.get('descripcion', 'N/A')
            total = item.get('total', 'N/A')
            response_text += f"{i}. {desc} - {total}\n"
        if len(items) > 5:
            response_text += f"... y {len(items) - 5} items más\n"
        response_text += "\n"
    
    response_text += f"🔗 *ID Documento:* `{result.get('document_id')}`"
    
    return response_text

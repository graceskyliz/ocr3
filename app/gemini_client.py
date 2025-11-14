# app/gemini_client.py
import os
import json
import re
from typing import Dict, Any, Optional, List
from decimal import Decimal, InvalidOperation
from datetime import datetime
from PIL import Image
import google.generativeai as genai
from fastapi import HTTPException

def configure_gemini(api_key: str):
    """Configura el cliente de Gemini con la API key."""
    genai.configure(api_key=api_key)

def analyze_document_gemini(image_path: str, doc_kind: str = "factura") -> Dict[str, Any]:
    """
    Analiza un documento (PDF convertido a imagen o imagen directa) usando Gemini Vision.
    
    Args:
        image_path: Ruta local al archivo de imagen
        doc_kind: Tipo de documento ('boleta', 'factura', 'excel')
    
    Returns:
        Diccionario con la información extraída estructurada
    """
    try:
        # Cargar imagen
        img = Image.open(image_path)
        
        # Configurar el modelo
        model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        # Prompt especializado según el tipo de documento
        if doc_kind == "boleta":
            prompt = """Analiza esta boleta de venta peruana y extrae EXACTAMENTE la siguiente información en formato JSON:

{
  "provider": {
    "ruc": "RUC de 11 dígitos del emisor",
    "razon_social": "Razón social del emisor"
  },
  "invoice": {
    "numero": "Número de boleta (formato B001-12345678 o similar)",
    "fecha": "Fecha de emisión en formato YYYY-MM-DD",
    "moneda": "PEN o USD",
    "subtotal": "Monto subtotal si está disponible",
    "igv": "Monto IGV si está disponible",
    "total": "Monto total de la boleta"
  },
  "items": [
    {
      "descripcion": "Descripción del producto/servicio",
      "cantidad": "Cantidad",
      "precio_unitario": "Precio unitario",
      "total": "Total del item"
    }
  ]
}

IMPORTANTE:
- Si un campo no está visible o legible, usa null
- Los montos deben ser números sin símbolos de moneda
- La fecha debe estar en formato ISO (YYYY-MM-DD)
- Extrae TODOS los items que aparezcan en la boleta
- Responde SOLO con el JSON, sin texto adicional"""

        elif doc_kind == "factura":
            prompt = """Analiza esta factura peruana y extrae EXACTAMENTE la siguiente información en formato JSON:

{
  "provider": {
    "ruc": "RUC de 11 dígitos del emisor",
    "razon_social": "Razón social del emisor",
    "direccion": "Dirección del emisor si está disponible"
  },
  "cliente": {
    "ruc": "RUC del cliente si está disponible",
    "razon_social": "Razón social del cliente"
  },
  "invoice": {
    "numero": "Número de factura (formato F001-12345678 o similar)",
    "fecha": "Fecha de emisión en formato YYYY-MM-DD",
    "fecha_vencimiento": "Fecha de vencimiento si está disponible en formato YYYY-MM-DD",
    "moneda": "PEN o USD",
    "subtotal": "Monto subtotal (base imponible)",
    "igv": "Monto IGV/impuesto",
    "total": "Monto total de la factura",
    "forma_pago": "Forma de pago si está disponible"
  },
  "items": [
    {
      "descripcion": "Descripción del producto/servicio",
      "cantidad": "Cantidad",
      "precio_unitario": "Precio unitario",
      "total": "Total del item"
    }
  ]
}

IMPORTANTE:
- Si un campo no está visible o legible, usa null
- Los montos deben ser números sin símbolos de moneda
- Las fechas deben estar en formato ISO (YYYY-MM-DD)
- Extrae TODOS los items que aparezcan en la factura
- Responde SOLO con el JSON, sin texto adicional"""

        else:  # genérico
            prompt = """Analiza este documento financiero peruano (boleta o factura) y extrae la información en formato JSON:

{
  "provider": {
    "ruc": "RUC del emisor",
    "razon_social": "Razón social del emisor"
  },
  "invoice": {
    "numero": "Número del comprobante",
    "fecha": "Fecha en formato YYYY-MM-DD",
    "moneda": "PEN o USD",
    "total": "Monto total"
  },
  "items": []
}

Responde SOLO con el JSON, sin texto adicional."""

        # Generar contenido con Gemini
        response = model.generate_content([prompt, img])
        
        # Extraer el texto de la respuesta
        raw_text = response.text.strip()
        
        # Limpiar el texto para extraer solo el JSON
        json_text = _extract_json_from_response(raw_text)
        
        # Parsear el JSON
        try:
            parsed_data = json.loads(json_text)
        except json.JSONDecodeError as e:
            # Si falla el parseo, intentar extraer información básica del texto
            parsed_data = _fallback_parse(raw_text, doc_kind)
        
        # Normalizar y validar los datos
        normalized_data = _normalize_parsed_data(parsed_data, doc_kind)
        
        return {
            "engine": "gemini-vision",
            "confidence": 0.85,  # Gemini generalmente tiene alta confianza
            "raw_text": raw_text[:5000],  # Primeros 5000 caracteres
            "parsed": normalized_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar documento con Gemini: {str(e)}"
        )

def _extract_json_from_response(text: str) -> str:
    """Extrae el JSON de la respuesta de Gemini."""
    # Buscar JSON entre ```json y ``` o entre { y }
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    json_match = re.search(r'```\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    # Si no hay markdown, buscar el primer objeto JSON
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    return text

def _fallback_parse(text: str, doc_kind: str) -> Dict[str, Any]:
    """Parser de respaldo si falla el JSON."""
    return {
        "provider": {
            "ruc": _extract_ruc(text)
        },
        "invoice": {
            "numero": _extract_invoice_number(text, doc_kind),
            "fecha": _extract_date(text),
            "moneda": _extract_currency(text),
            "total": _extract_total(text)
        },
        "items": []
    }

def _normalize_parsed_data(data: Dict[str, Any], doc_kind: str) -> Dict[str, Any]:
    """Normaliza y valida los datos parseados."""
    normalized = {
        "provider": data.get("provider", {}),
        "invoice": data.get("invoice", {}),
        "items": data.get("items", [])
    }
    
    # Agregar cliente si existe (solo para facturas)
    if doc_kind == "factura" and "cliente" in data:
        normalized["cliente"] = data["cliente"]
    
    # Normalizar montos a string
    if normalized["invoice"].get("total"):
        try:
            total = str(normalized["invoice"]["total"]).replace(",", "")
            normalized["invoice"]["total"] = total
        except (ValueError, TypeError, AttributeError):
            pass
    
    if normalized["invoice"].get("subtotal"):
        try:
            subtotal = str(normalized["invoice"]["subtotal"]).replace(",", "")
            normalized["invoice"]["subtotal"] = subtotal
        except (ValueError, TypeError, AttributeError):
            pass
    
    if normalized["invoice"].get("igv"):
        try:
            igv = str(normalized["invoice"]["igv"]).replace(",", "")
            normalized["invoice"]["igv"] = igv
        except (ValueError, TypeError, AttributeError):
            pass
    
    return normalized

# Funciones auxiliares de extracción (fallback)
def _extract_ruc(text: str) -> Optional[str]:
    m = re.search(r"(?:\bRUC\b|R\.?U\.?C\.?)\D*?(\d{11})", text, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r"\b(\d{11})\b", text)
    if m:
        return m.group(1)
    return None

def _extract_currency(text: str) -> str:
    if re.search(r"\bUSD\b|\bUS?\$\b|\bDOLARES?\b", text, re.IGNORECASE):
        return "USD"
    if re.search(r"\bPEN\b|\bSOLES?\b|\bS\/", text, re.IGNORECASE):
        return "PEN"
    return "PEN"  # Por defecto en Perú

def _extract_total(text: str) -> Optional[str]:
    pats = [
        r"TOTAL[:\s]*([S\$]*\s*[\d\.\,]+)",
        r"IMPORTE\s+TOTAL[:\s]*([S\$]*\s*[\d\.\,]+)"
    ]
    for p in pats:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            v = re.sub(r"[S$ ]", "", m.group(1))
            return v
    return None

def _extract_date(text: str) -> Optional[str]:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    m = re.search(r"(\d{2}/\d{2}/\d{4})", text)
    if m:
        try:
            dt = datetime.strptime(m.group(1), "%d/%m/%Y")
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            pass
    return None

def _extract_invoice_number(text: str, doc_kind: str) -> Optional[str]:
    if doc_kind == "boleta":
        m = re.search(r"\b(B\d{3}-\d+)\b", text, re.IGNORECASE)
    else:
        m = re.search(r"\b(F\d{3}-\d+)\b", text, re.IGNORECASE)
    
    if m:
        return m.group(1).upper()
    
    m = re.search(r"\b([A-Z]\d{3}-\d+)\b", text)
    if m:
        return m.group(1).upper()
    
    return None

def convert_pdf_to_images(pdf_path: str) -> List[str]:
    """
    Convierte un PDF a imágenes (una por página).
    Retorna lista de rutas a las imágenes temporales.
    """
    from pdf2image import convert_from_path
    import tempfile
    
    images = convert_from_path(pdf_path, dpi=300)
    temp_paths = []
    
    for i, img in enumerate(images):
        temp_path = os.path.join(tempfile.gettempdir(), f"page_{i}_{os.getpid()}.png")
        img.save(temp_path, "PNG")
        temp_paths.append(temp_path)
    
    return temp_paths

def analyze_pdf_with_gemini(pdf_path: str, doc_kind: str = "factura") -> Dict[str, Any]:
    """
    Analiza un PDF convirtiéndolo a imágenes y procesando con Gemini.
    Solo procesa la primera página por defecto.
    """
    temp_images = []
    try:
        temp_images = convert_pdf_to_images(pdf_path)
        
        if not temp_images:
            raise HTTPException(status_code=422, detail="No se pudo convertir el PDF a imágenes")
        
        # Procesar solo la primera página (donde suele estar la info principal)
        result = analyze_document_gemini(temp_images[0], doc_kind)
        
        return result
        
    finally:
        # Limpiar imágenes temporales
        for img_path in temp_images:
            try:
                if os.path.exists(img_path):
                    os.remove(img_path)
            except OSError:
                pass

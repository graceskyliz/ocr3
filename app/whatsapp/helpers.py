# app/whatsapp/helpers.py
"""Funciones auxiliares para WhatsApp"""
import logging

log = logging.getLogger(__name__)


def get_welcome_message() -> str:
    """Mensaje de bienvenida para nuevos usuarios"""
    return (
        "👋 *¡Hola! Te acabo de registrar automáticamente.*\n\n"
        "Puedes enviarme fotos o PDFs de boletas/facturas y las procesaré por ti.\n\n"
        "📸 Envía una *imagen* de tu documento\n"
        "📄 O envía un *PDF*\n\n"
        "Te responderé con toda la información extraída en segundos. ⚡"
    )


def get_instructions_message() -> str:
    """Mensaje de instrucciones para usuarios existentes"""
    return (
        "📋 *Instrucciones de uso:*\n\n"
        "✅ Envíame una foto o PDF de:\n"
        "   • Facturas\n"
        "   • Boletas\n"
        "   • Recibos\n\n"
        "🤖 Yo extraeré automáticamente:\n"
        "   • RUC y razón social\n"
        "   • Número y fecha\n"
        "   • Montos e items\n"
        "   • Y mucho más...\n\n"
        "💡 *Tip:* Asegúrate de que la imagen sea clara y legible."
    )


def get_processing_message() -> str:
    """Mensaje mientras se procesa el documento"""
    return "⏳ *Procesando tu documento con OCR...*\n\nUn momento por favor. ⚙️"


def get_unsupported_format_message() -> str:
    """Mensaje para formatos no soportados"""
    return (
        "⚠️ *Este tipo de mensaje no es soportado.*\n\n"
        "Por favor envía:\n"
        "📸 Una imagen (JPG, PNG)\n"
        "📄 Un archivo PDF\n\n"
        "Si tienes problemas, escribe 'ayuda' para más información."
    )


def get_error_message(error_detail: str = None) -> str:
    """Mensaje de error genérico"""
    base_message = (
        "❌ *Hubo un problema al procesar tu documento.*\n\n"
        "Por favor intenta nuevamente. Si el problema persiste, "
        "asegúrate de que:\n"
        "• La imagen sea clara\n"
        "• El PDF no esté dañado\n"
        "• El archivo no sea muy grande\n"
    )
    
    if error_detail:
        base_message += f"\n\n📝 *Detalle:* {error_detail}"
    
    return base_message


def sanitize_phone_number(phone: str) -> str:
    """
    Sanitiza el número de teléfono para almacenamiento.
    
    Args:
        phone: Número de teléfono en cualquier formato
    
    Returns:
        Número limpio sin + ni espacios
    """
    return phone.replace("+", "").replace(" ", "").replace("-", "")

Necesito que implementes en FastAPI un endpoint webhook para WhatsApp Cloud API:

1. Ruta: POST /webhook/whatsapp  
2. Ruta de verificación: GET /webhook/whatsapp (para Meta Webhook Verification)
   - Debe validar el token enviado desde Meta:
     GET params:
       - "hub.mode"
       - "hub.challenge"
       - "hub.verify_token"
   - Si verify_token = "thesaurus-whatsapp", devolver hub.challenge.

3. Cuando llegue un mensaje:
   - Detectar si es texto, imagen o documento.
   - Si es imagen o PDF, obtener la media_id.
   - Llamar a la API de Meta para descargar la media:
       GET https://graph.facebook.com/v17.0/{media_id}
       Luego descargar usando la URL que responde.
   - Guardar el archivo en mi storage local o bucket S3.
   - Enviar este archivo a mi pipeline de OCR (usa una función llamada process_document(file_path))
   - Con la respuesta del OCR, enviar un mensaje por WhatsApp al usuario:
       POST https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages
       JSON:
         {
           "messaging_product": "whatsapp",
           "to": "<numero_usuario>",
           "text": { "body": "<respuesta del OCR>" }
         }

4. Crear una función auxiliar send_whatsapp_message(to, text).
5. Crear una función download_media(media_id) que obtenga y descargue la imagen/PDF.
6. Todo con manejo de errores.

Variables necesarias (úsalas desde .env):
   WHATSAPP_TOKEN
   PHONE_NUMBER_ID
   APP_VERIFY_TOKEN = "thesaurus-whatsapp"

Genera el archivo FastAPI listo para pegar, bien estructurado, con comentarios y funciones separadas.

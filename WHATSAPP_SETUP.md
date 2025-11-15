# Configuración de WhatsApp Cloud API

Este documento explica cómo configurar el webhook de WhatsApp Business Cloud API para procesar boletas y facturas.

## 📋 Requisitos Previos

1. **Cuenta de Meta for Developers**
   - Crear cuenta en [developers.facebook.com](https://developers.facebook.com)
   - Crear una aplicación de tipo "Business"

2. **WhatsApp Business API**
   - Activar el producto "WhatsApp" en tu aplicación
   - Obtener número de teléfono de prueba o conectar tu número business

3. **Tokens y Credenciales**
   - Token de acceso (WHATSAPP_TOKEN)
   - ID del número de teléfono (PHONE_NUMBER_ID)
   - Token de verificación (APP_VERIFY_TOKEN)

## 🚀 Configuración Paso a Paso

### 1. Obtener Credenciales de WhatsApp

1. Ir a [Meta for Developers](https://developers.facebook.com/)
2. Seleccionar tu aplicación
3. En el panel izquierdo, ir a **WhatsApp > Inicio rápido**
4. Copiar:
   - **Token de acceso temporal** (válido 24 horas) o generar uno permanente
   - **ID del número de teléfono** (Phone Number ID)
   - **Número de prueba** para testing

### 2. Configurar Variables de Entorno

Editar el archivo `.env` en la raíz del proyecto:

```env
# WhatsApp Cloud API Configuration
WHATSAPP_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
PHONE_NUMBER_ID=123456789012345
APP_VERIFY_TOKEN=thesaurus-whatsapp
```

**Importante:**
- `WHATSAPP_TOKEN`: Token de acceso de WhatsApp Business API
- `PHONE_NUMBER_ID`: ID del número de teléfono de WhatsApp Business
- `APP_VERIFY_TOKEN`: Token personalizado para verificar el webhook (puede ser cualquier string seguro)

### 3. Exponer tu Servidor

Para que Meta pueda enviar webhooks a tu servidor local, necesitas exponerlo públicamente:

#### Opción A: ngrok (Recomendado para desarrollo)

```powershell
# Instalar ngrok desde https://ngrok.com/download
ngrok http 9000
```

Copiar la URL pública generada (ej: `https://abc123.ngrok.io`)

#### Opción B: Servidor en la nube
- Desplegar en AWS, Google Cloud, Azure, Railway, etc.
- Asegurarse de que el puerto 9000 esté accesible públicamente

### 4. Configurar el Webhook en Meta

1. Ir a **WhatsApp > Configuración > Configuración de Webhook**
2. Hacer clic en **Editar**
3. Configurar:
   ```
   URL de devolución de llamada: https://tu-dominio.com/webhook/whatsapp
   Token de verificación: thesaurus-whatsapp
   ```
4. Hacer clic en **Verificar y guardar**

Si la verificación es exitosa, verás un mensaje de confirmación ✅

### 5. Suscribirse a Eventos

En la misma página de configuración de webhook:

1. Ir a la sección **Campos del webhook**
2. Hacer clic en **Administrar** o **Suscribirse**
3. Activar los siguientes eventos:
   - ✅ **messages** (requerido)
   - ✅ **message_status** (opcional, para confirmaciones de entrega)

4. Guardar cambios

## 🧪 Prueba de Funcionamiento

### 1. Verificar que el servidor esté corriendo

```powershell
# Asegurarse de que el servidor esté activo
cd c:\Users\ASUS\ocr3
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
```

### 2. Probar el endpoint de verificación

```powershell
# Probar manualmente el endpoint de verificación
curl "http://localhost:9000/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=thesaurus-whatsapp&hub.challenge=12345"
# Debe retornar: 12345
```

### 3. Enviar mensaje de prueba desde WhatsApp

1. Abrir WhatsApp en tu teléfono
2. Enviar un mensaje al número de prueba proporcionado por Meta
3. Responderás automáticamente con instrucciones

### 4. Enviar una imagen de boleta/factura

1. Tomar foto de una boleta o factura
2. Enviarla por WhatsApp al número de prueba
3. Esperar procesamiento (aprox. 5-10 segundos)
4. Recibir resultados del OCR formateados

## 📊 Monitoreo y Logs

### Ver logs del servidor

```powershell
# Los logs mostrarán:
# - Mensajes recibidos
# - Procesamiento de OCR
# - Errores si los hay
# - Respuestas enviadas
```

### Verificar webhooks en Meta

1. Ir a **WhatsApp > Configuración**
2. Ver **Registro de webhooks**
3. Revisar llamadas recientes y respuestas

## 🔧 Solución de Problemas

### Error: "WHATSAPP_TOKEN no está configurado"

**Solución:** Verificar que el archivo `.env` tenga la variable `WHATSAPP_TOKEN` correctamente configurada.

```powershell
# Verificar variables de entorno
cat .env
```

### Error: "Verificación de webhook fallida"

**Causas posibles:**
1. `APP_VERIFY_TOKEN` en `.env` no coincide con el configurado en Meta
2. La URL del webhook está mal configurada
3. El servidor no está accesible públicamente

**Solución:**
```powershell
# Verificar que el token sea correcto
echo $env:APP_VERIFY_TOKEN

# Probar el endpoint manualmente
curl "https://tu-dominio.com/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=thesaurus-whatsapp&hub.challenge=test123"
```

### Error: "Error al descargar archivo"

**Causas posibles:**
1. Token de WhatsApp expirado (tokens temporales duran 24h)
2. Permisos insuficientes
3. Media ID inválido

**Solución:**
1. Generar token de acceso permanente:
   - Ir a **WhatsApp > Configuración > Token de acceso**
   - Generar nuevo token permanente
   - Actualizar `WHATSAPP_TOKEN` en `.env`

### No se reciben mensajes

**Verificar:**
1. Webhook configurado correctamente en Meta
2. Servidor accesible públicamente (probar con `curl` desde fuera)
3. Eventos "messages" suscritos en Meta
4. Logs del servidor para ver errores

```powershell
# Ver logs en tiempo real
uvicorn app.main:app --reload --log-level debug
```

## 🔐 Seguridad en Producción

### 1. Token de acceso permanente

En lugar de usar tokens temporales (24h), generar un token permanente:

1. Ir a **WhatsApp > Configuración**
2. Generar token de sistema con permisos `whatsapp_business_messaging`
3. Guardar de forma segura (no commitear al repositorio)

### 2. Validar firma de webhook

Para mayor seguridad, validar que los webhooks vengan realmente de Meta:

```python
# Agregar a app/routers/whatsapp.py
import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verificar firma SHA256 del webhook"""
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected_signature}", signature)
```

### 3. Rate limiting

Implementar límites de peticiones para evitar abusos:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/whatsapp")
@limiter.limit("10/minute")
async def handle_webhook(request: Request):
    # ...
```

### 4. Variables de entorno seguras

**Nunca** commitear `.env` con credenciales reales:

```bash
# Agregar a .gitignore
.env
.env.local
.env.production
```

Usar servicios de secrets management en producción:
- AWS Secrets Manager
- Google Cloud Secret Manager
- Azure Key Vault
- HashiCorp Vault

## 📚 Recursos Adicionales

- [Documentación oficial WhatsApp Business API](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Guía de webhooks](https://developers.facebook.com/docs/graph-api/webhooks)
- [Referencia de mensajes](https://developers.facebook.com/docs/whatsapp/cloud-api/reference/messages)
- [Códigos de error](https://developers.facebook.com/docs/whatsapp/cloud-api/support/error-codes)

## 🎯 Flujo Completo

```
Usuario (WhatsApp)
     |
     | 1. Envía imagen/PDF
     v
Meta WhatsApp Cloud API
     |
     | 2. POST /webhook/whatsapp
     v
Tu servidor (FastAPI)
     |
     | 3. Descarga media
     | 4. Guarda en ./uploads/
     | 5. Procesa con Gemini OCR
     | 6. Formatea resultados
     |
     | 7. POST a WhatsApp API
     v
Meta WhatsApp Cloud API
     |
     | 8. Entrega mensaje
     v
Usuario (WhatsApp)
```

## ✅ Checklist de Configuración

- [ ] Cuenta de Meta for Developers creada
- [ ] Aplicación de WhatsApp Business creada
- [ ] Token de acceso obtenido (WHATSAPP_TOKEN)
- [ ] Phone Number ID obtenido (PHONE_NUMBER_ID)
- [ ] Variables en `.env` configuradas
- [ ] Servidor expuesto públicamente (ngrok o cloud)
- [ ] Webhook configurado en Meta
- [ ] Token de verificación coincide
- [ ] Eventos "messages" suscritos
- [ ] Prueba de mensaje de texto exitosa
- [ ] Prueba de imagen/PDF exitosa
- [ ] Logs monitoreados sin errores

¡Todo listo! 🎉 Ahora puedes recibir boletas y facturas por WhatsApp y procesarlas automáticamente con OCR.

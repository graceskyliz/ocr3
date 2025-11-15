# Guía de Implementación Mejorada: Auto-Onboarding WhatsApp

## 🎯 Resumen de Cambios Implementados

Se ha mejorado completamente la integración de WhatsApp siguiendo las especificaciones de `whatsapp_onboarding_prompt.md`:

### ✅ 1. Estructura de Módulos Creada

```
app/
 └── whatsapp/
       ├── __init__.py
       ├── router.py          # Endpoint webhook principal
       ├── onboarding.py      # Lógica de auto-onboarding
       ├── processor.py       # Procesamiento de documentos
       ├── client.py          # Cliente WhatsApp API
       └── helpers.py         # Funciones auxiliares
```

### ✅ 2. Modelos de Base de Datos

**Nuevo archivo:** `app/auth_models.py`

- `Tenant`: Modelo para tenants/empresas con soporte WhatsApp
- `User`: Modelo para usuarios con múltiples fuentes (whatsapp, web, api)

**Campos clave agregados:**
- `Tenant.whatsapp_number`: Número único de WhatsApp
- `User.source`: Origen del registro (whatsapp, web, api)
- `User.phone`: Teléfono del usuario
- `User.role`: Rol del usuario (owner, admin, user)

### ✅ 3. Auto-Onboarding Completo

**Archivo:** `app/whatsapp/onboarding.py`

Función principal: `get_or_create_tenant_by_whatsapp(db, whatsapp_number)`

**Flujo implementado:**
1. Busca tenant existente por `whatsapp_number`
2. Si no existe, crea automáticamente:
   - Nuevo `Tenant` con UUID único
   - Nuevo `User` tipo "owner" asociado
   - Relación `phone_number → tenant_id`
3. Retorna `(Tenant, User, is_new)` donde `is_new` indica si es registro nuevo

### ✅ 4. Procesamiento Mejorado

**Archivo:** `app/whatsapp/processor.py`

Función: `process_whatsapp_media()`

**Flujo completo implementado:**
1. ✅ Descarga archivo de WhatsApp API
2. ✅ Calcula hash SHA256
3. ✅ Guarda en almacenamiento local (`./uploads/`)
4. ✅ Crea registro en `documents.documents`
5. ✅ Procesa con Gemini OCR
6. ✅ Guarda resultado en `extractor.extractions`
7. ✅ Mapea a finance (providers, invoices, items)
8. ✅ Retorna resultado estructurado

**Persistencia garantizada:**
- ✅ `documents.documents`: Archivo guardado con metadata
- ✅ `extractor.extractions`: Resultado OCR en JSONB
- ✅ `finance.providers`: RUC y razón social
- ✅ `finance.invoices`: Factura completa
- ✅ `finance.invoice_items`: Items de la factura

### ✅ 5. Respuestas Formateadas

**Archivo:** `app/whatsapp/helpers.py`

Mensajes implementados:
- `get_welcome_message()`: Bienvenida para nuevos usuarios
- `get_instructions_message()`: Instrucciones de uso
- `get_processing_message()`: Mensaje mientras procesa
- `get_unsupported_format_message()`: Formato no válido
- `get_error_message()`: Errores genéricos

**Formato de respuesta OCR:**
```
✅ *Documento procesado exitosamente*

📄 *Motor:* Gemini Vision
📊 *Confianza:* 95%

💼 *Proveedor*
RUC: 20123456789
Razón Social: Empresa SAC

📋 *Documento*
Serie: F001
Número: 00123
Total: S/ 450.00

📦 *Items (3):*
1. Producto A - 200.00
2. Producto B - 150.00
3. Producto C - 100.00

🔗 *ID Documento:* `abc-123-def`
```

### ✅ 6. Endpoint Webhook Mejorado

**Archivo:** `app/whatsapp/router.py`

**GET `/webhook/whatsapp`:**
- Verificación de webhook para Meta
- Valida `hub.verify_token` = "thesaurus-whatsapp"
- Retorna `hub.challenge` si válido

**POST `/webhook/whatsapp`:**
- Auto-onboarding automático por número
- Mensaje de bienvenida para nuevos usuarios
- Procesamiento de texto, imágenes y PDFs
- Comandos especiales: "ayuda", "hola"
- Guardado completo en BD
- Respuestas formateadas

### ✅ 7. Manejo de Errores

Casos implementados:
- ✅ Usuario nuevo → registro automático + bienvenida
- ✅ Archivos corruptos → mensaje de error detallado
- ✅ Formato no soportado → mensaje de advertencia
- ✅ Mensajes vacíos → instrucciones
- ✅ Timeout OCR (30s) → timeout en httpx
- ✅ Errores de BD → rollback automático
- ✅ Errores de WhatsApp API → logging y respuesta

### ✅ 8. Logs Implementados

Todos los módulos tienen logging configurado:
```python
log.info(f"Usuario nuevo registrado: {from_number}")
log.info(f"Documento guardado: {document.id}")
log.info(f"Extracción guardada: {extraction.id}")
log.error(f"Error procesando media: {e}", exc_info=True)
```

## 📋 Migraciones SQL Necesarias

**Archivo:** `scripts/add_whatsapp_onboarding.sql`

Ejecutar antes de usar:
```bash
psql -h localhost -p 5433 -U postgres -d postgres -f scripts/add_whatsapp_onboarding.sql
```

Agrega:
- Campo `whatsapp_number` a `auth.tenants`
- Campos `phone`, `source`, `role` a `auth.users`
- Índices para búsqueda rápida
- Permite `email` y `password_hash` NULL

## 🚀 Cómo Probar

### 1. Configurar Variables de Entorno

Actualizar `.env`:
```env
# WhatsApp Cloud API Configuration
WHATSAPP_TOKEN=tu_token_de_whatsapp_aqui
PHONE_NUMBER_ID=tu_phone_number_id_aqui
APP_VERIFY_TOKEN=thesaurus-whatsapp
```

### 2. Ejecutar Migraciones

```powershell
psql -h localhost -p 5433 -U postgres -d postgres -f scripts/add_whatsapp_onboarding.sql
```

### 3. Reiniciar Servidor

```powershell
# El servidor ya está corriendo, reiniciará automáticamente con --reload
```

### 4. Exponer con ngrok

```powershell
ngrok http 9000
```

### 5. Configurar Webhook en Meta

1. Ir a [Meta for Developers](https://developers.facebook.com/)
2. WhatsApp > Configuración > Webhook
3. URL: `https://tu-url-ngrok.com/webhook/whatsapp`
4. Token: `thesaurus-whatsapp`
5. Suscribirse a evento: `messages`

### 6. Probar Flujo Completo

1. **Mensaje de texto inicial:**
   - Usuario: "Hola"
   - Bot: Mensaje de bienvenida + auto-registro

2. **Enviar imagen de factura:**
   - Usuario: [envía foto]
   - Bot: "Procesando..."
   - Bot: Resultado formateado con todos los datos

3. **Verificar en BD:**
   ```sql
   SELECT * FROM auth.tenants WHERE whatsapp_number = '51999999999';
   SELECT * FROM auth.users WHERE source = 'whatsapp';
   SELECT * FROM documents.documents ORDER BY id DESC LIMIT 1;
   SELECT * FROM extractor.extractions ORDER BY id DESC LIMIT 1;
   SELECT * FROM finance.invoices ORDER BY id DESC LIMIT 1;
   ```

## 📊 Diferencias con Implementación Anterior

| Característica | Anterior | Mejorada |
|----------------|----------|----------|
| Router | `app/routers/whatsapp.py` | `app/whatsapp/router.py` |
| Onboarding | Manual | **Automático** |
| Persistencia | Solo uploads | **BD completa** |
| Tenant creation | No | **Sí** |
| User creation | No | **Sí** |
| Extraction guardada | No | **Sí en BD** |
| Finance mapping | No | **Sí automático** |
| Mensajes formatados | Básico | **Rico con emojis** |
| Estructura | 1 archivo | **5 módulos** |

## 🎯 Comportamiento Esperado

### Usuario Nuevo
```
Usuario: "Hola"
Bot:
👋 ¡Hola! Te acabo de registrar automáticamente.

Puedes enviarme fotos o PDFs de boletas/facturas y las procesaré por ti.

📸 Envía una imagen de tu documento
📄 O envía un PDF

Te responderé con toda la información extraída en segundos. ⚡
```

### Usuario Existente
```
Usuario: [envía imagen]
Bot:
⏳ Procesando tu documento con OCR...
Un momento por favor. ⚙️

[Después de 5-10 segundos]

✅ Documento procesado exitosamente

📄 Motor: gemini
📊 Confianza: 95%

💼 Proveedor
RUC: 20123456789
Razón Social: Mi Empresa SAC

📋 Documento
Serie: F001
Número: 00123
Total: S/ 450.00

📦 Items (2):
1. Laptop - 350.00
2. Mouse - 100.00

🔗 ID Documento: `abc-123-def`
```

## ✅ Checklist de Implementación

- [x] Modelos `Tenant` y `User` creados
- [x] Módulo `whatsapp/` estructurado
- [x] Auto-onboarding implementado
- [x] Procesamiento con persistencia en BD
- [x] Guardado en `documents.documents`
- [x] Guardado en `extractor.extractions`
- [x] Mapeo automático a finance
- [x] Respuestas formateadas
- [x] Manejo de errores completo
- [x] Logs detallados
- [x] Comandos especiales (ayuda, hola)
- [x] SQL migrations creadas
- [x] Router actualizado en `main.py`
- [ ] Ejecutar migraciones SQL (manual)
- [ ] Configurar tokens WhatsApp (manual)
- [ ] Exponer con ngrok (manual)
- [ ] Configurar webhook en Meta (manual)

## 🔧 Próximos Pasos

1. **Ejecutar migraciones:**
   ```powershell
   psql -h localhost -p 5433 -U postgres -d postgres -f scripts/add_whatsapp_onboarding.sql
   ```

2. **Obtener tokens de WhatsApp:**
   - Ir a Meta for Developers
   - Copiar `WHATSAPP_TOKEN` y `PHONE_NUMBER_ID`
   - Actualizar `.env`

3. **Exponer servidor:**
   ```powershell
   ngrok http 9000
   ```

4. **Configurar webhook en Meta**

5. **Probar con mensaje de prueba**

¡Todo listo para auto-onboarding completo! 🎉

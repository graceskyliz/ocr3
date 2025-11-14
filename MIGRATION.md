# Migración a Gemini Vision API - Resumen

## ✅ Cambios Completados

### 1. **Dependencias Actualizadas**
- ❌ Removido: `boto3` (AWS SDK)
- ✅ Agregado: `google-generativeai` (Gemini API)
- ✅ Agregado: `pdf2image` (conversión de PDF)
- ✅ Agregado: `pytesseract` (fallback OCR)
- ✅ Agregado: `python-dotenv` (variables de entorno)

### 2. **Nuevos Archivos Creados**
- `app/gemini_client.py` - Cliente para Gemini Vision API
- `app/storage_local.py` - Almacenamiento local (reemplaza S3)
- `TESTING.md` - Ejemplos de uso
- `start.bat` / `start.sh` - Scripts de inicio rápido
- `.env` - Configuración con tu API key de Gemini

### 3. **Archivos Modificados**
- `app/settings.py` - Nueva configuración para Gemini y storage local
- `app/routers/documents.py` - Subida de archivos local (sin S3)
- `app/routers/ocr.py` - Procesamiento con Gemini Vision
- `app/main.py` - CORS y carga de variables de entorno
- `README.md` - Documentación actualizada
- `.gitignore` - Proteger archivos sensibles
- `requirements.txt` - Dependencias actualizadas

### 4. **Archivos Obsoletos** (puedes eliminarlos si quieres)
- `app/textract_client.py` - Ya no se usa AWS Textract
- `app/s3_client.py` - Ya no se usa S3
- `app/storage.py` - Reemplazado por `storage_local.py`

## 🔑 Configuración Aplicada

Tu archivo `.env` está configurado con:
```env
GEMINI_API_KEY=AIzaSyDWKxfXj9_dsSuVpfQTaPUng8Rj1hIV8Pg
DB_HOST=postgres
DB_PORT=5433
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=270504949096933
UPLOAD_DIR=./uploads
MAX_UPLOAD_MB=15
ALLOWED_MIME=application/pdf,image/jpeg,image/png
```

## 🚀 Cómo Iniciar el Servicio

### Opción 1: Script de inicio (Windows)
```bash
start.bat
```

### Opción 2: Comando directo
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Opción 3: Producción con Gunicorn
```bash
gunicorn -c gunicorn_conf.py app.main:app
```

## 📡 Endpoints Disponibles

### 1. Health Check
```
GET http://localhost:8080/health
```

### 2. Subir Documento
```
POST http://localhost:8080/documents/upload
Content-Type: multipart/form-data

Campos:
- file: archivo (PDF, JPG, PNG)
- tenant_id: UUID del tenant
- doc_kind: 'boleta' o 'factura'
```

### 3. Procesar OCR
```
POST http://localhost:8080/ocr/process/{doc_id}
```

### 4. Documentación Interactiva
```
http://localhost:8080/docs
```

## 🔄 Flujo de Integración con Frontend

```javascript
// 1. Subir documento
const uploadData = await uploadDocument(file, tenantId, 'boleta');

// 2. Procesar con OCR (Gemini Vision)
const ocrData = await processOCR(uploadData.id);

// 3. Enviar a microservicio 'insights'
const insights = await sendToInsights(ocrData.data);
```

## 📊 Estructura de Datos Extraídos

### Boletas
- RUC del emisor
- Razón social
- Número de boleta
- Fecha
- Moneda (PEN/USD)
- Subtotal, IGV, Total
- Items detallados

### Facturas
- RUC emisor y cliente
- Razón social emisor y cliente
- Número de factura
- Fechas (emisión, vencimiento)
- Moneda (PEN/USD)
- Subtotal, IGV, Total
- Forma de pago
- Items detallados

## 🎯 Ventajas de Gemini Vision API

1. **No requiere AWS** - Sin costos de S3 ni Textract
2. **Almacenamiento local** - Mayor control de archivos
3. **OCR multimodal** - Gemini entiende contexto visual y texto
4. **API simple** - Una sola API key
5. **Extracción estructurada** - JSON directo con los campos necesarios
6. **Soporta múltiples formatos** - PDF, JPG, PNG nativamente

## ⚠️ Requisitos Adicionales

### Windows
Si usas PDF, necesitas instalar Poppler:
1. Descarga: https://github.com/oschwartz10612/poppler-windows/releases/
2. Extrae en `C:\Program Files\poppler`
3. Agrega al PATH: `C:\Program Files\poppler\Library\bin`

### Linux
```bash
sudo apt-get install poppler-utils
```

### Mac
```bash
brew install poppler
```

## 📝 Próximos Pasos

1. **Iniciar el servicio**: `start.bat` o `uvicorn app.main:app --reload`
2. **Probar en Swagger**: http://localhost:8080/docs
3. **Integrar con tu frontend**: Ver ejemplos en `TESTING.md`
4. **Conectar con microservicio 'insights'**: Enviar `ocrData.data` para análisis

## 🐛 Solución de Problemas

### Error: "GEMINI_API_KEY es requerida"
→ Verifica que tu archivo `.env` existe y tiene la API key

### Error: "Archivo no encontrado"
→ Asegúrate de crear el directorio `uploads/`

### Error al procesar PDF
→ Instala Poppler (ver sección Requisitos Adicionales)

### OCR con baja precisión
→ Usa imágenes de alta calidad (mínimo 300 DPI)
→ Asegúrate que el documento esté bien iluminado
→ Prefiere PDFs originales en lugar de escaneos

## 💡 Recomendaciones

1. **Seguridad**: Nunca subas `.env` a Git (ya está en `.gitignore`)
2. **CORS**: En producción, configura `allow_origins` con tu dominio específico
3. **Límites**: Gemini tiene límites de uso, revisa en https://makersuite.google.com/
4. **Backup**: Considera hacer backup del directorio `uploads/`
5. **Logs**: Revisa los logs para debugging (`log.info` en el código)

## 🎉 ¡Listo para Usar!

Tu servicio OCR está completamente migrado a Gemini Vision API y listo para integrarse con tu frontend y el microservicio de insights.

# OCR Service con Gemini Vision API

API de procesamiento OCR para documentos financieros (boletas, facturas) usando FastAPI, Google Gemini Vision API y PostgreSQL.

Este servicio está diseñado para integrarse con tu frontend para la subida de documentos (PDF, JPG, PNG) y extraer información estructurada que luego puede ser analizada por tu microservicio 'insights'.

## Requisitos Previos

- Python 3.9+
- PostgreSQL
- API Key de Google Gemini (https://makersuite.google.com/app/apikey)
- pip

## Instalación

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd ocr3
```

### 2. Crear entorno virtual

```bash
python -m venv venv
```

### 3. Activar entorno virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# API Key de Gemini
GEMINI_API_KEY=AIzaSyDWKxfXj9_dsSuVpfQTaPUng8Rj1hIV8Pg

# Base de datos PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aicfo
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña

# Configuración de uploads
UPLOAD_DIR=./uploads
MAX_UPLOAD_MB=15
ALLOWED_MIME=application/pdf,image/jpeg,image/png
```

**IMPORTANTE:** Nunca subas el archivo `.env` a tu repositorio. Asegúrate de que esté en tu `.gitignore`.

### 6. Configurar la base de datos

Ejecuta los scripts SQL para crear los esquemas e índices:

```bash
psql -h localhost -U tu_usuario -d aicfo -f scripts/create_schemas.sql
psql -h localhost -U tu_usuario -d aicfo -f scripts/create_indexes.sql
psql -h localhost -U tu_usuario -d aicfo -f scripts/add_kind_and_indexes.sql
```

### 7. Crear directorio de uploads

```bash
mkdir uploads
```

## Ejecución

### Modo Desarrollo

Ejecuta el servidor con uvicorn directamente:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Modo Producción

Ejecuta con Gunicorn:

```bash
gunicorn -c gunicorn_conf.py app.main:app
```

## Uso

Una vez levantado el servicio, puedes acceder a:

- **API**: http://localhost:8080
- **Documentación Swagger**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health

## Endpoints Principales

### Health Check
```http
GET /health
```
Verifica que el servicio está funcionando.

### Subir Documento
```http
POST /documents/upload
Content-Type: multipart/form-data

Form Data:
- file: archivo (PDF, JPG, PNG)
- tenant_id: ID del tenant
- user_id: ID del usuario (opcional)
- doc_kind: tipo de documento ('boleta' | 'factura')
```

**Ejemplo con cURL:**
```bash
curl -X POST "http://localhost:8080/documents/upload" \
  -F "file=@boleta.pdf" \
  -F "tenant_id=123e4567-e89b-12d3-a456-426614174000" \
  -F "doc_kind=boleta"
```

**Respuesta:**
```json
{
  "id": "doc-uuid",
  "storage_key": "tenant_id/doc_id/filename.pdf",
  "message": "Documento subido exitosamente. Use /ocr/process/{doc_id} para procesarlo."
}
```

### Procesar OCR
```http
POST /ocr/process/{doc_id}
```

Procesa el documento con Gemini Vision API y extrae la información estructurada.

**Ejemplo:**
```bash
curl -X POST "http://localhost:8080/ocr/process/doc-uuid"
```

**Respuesta:**
```json
{
  "engine": "gemini-vision",
  "doc_kind": "boleta",
  "invoice_id": "invoice-uuid",
  "confidence": 0.85,
  "data": {
    "provider": {
      "ruc": "20123456789",
      "razon_social": "EMPRESA EJEMPLO SAC"
    },
    "invoice": {
      "numero": "B001-00012345",
      "fecha": "2024-11-14",
      "moneda": "PEN",
      "total": "150.00"
    },
    "items": [
      {
        "descripcion": "Producto 1",
        "cantidad": "2",
        "precio_unitario": "75.00",
        "total": "150.00"
      }
    ]
  },
  "message": "OCR procesado exitosamente. Los datos están listos para enviar al microservicio 'insights'."
}
```

## Integración con Frontend

Tu frontend debe:

1. **Subir el documento**:
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('tenant_id', tenantId);
formData.append('doc_kind', 'boleta'); // o 'factura'

const uploadResponse = await fetch('http://localhost:8080/documents/upload', {
  method: 'POST',
  body: formData
});

const { id: docId } = await uploadResponse.json();
```

2. **Procesar OCR**:
```javascript
const ocrResponse = await fetch(`http://localhost:8080/ocr/process/${docId}`, {
  method: 'POST'
});

const ocrData = await ocrResponse.json();
```

3. **Enviar al microservicio 'insights'**:
```javascript
// Envía los datos extraídos a tu microservicio de análisis
const insightsResponse = await fetch('http://tu-servicio-insights/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    documentId: docId,
    ocrData: ocrData.data
  })
});
```

## Formatos Soportados

- ✅ **PDF** - Facturas y boletas en formato PDF
- ✅ **JPG/JPEG** - Imágenes de facturas y boletas
- ✅ **PNG** - Imágenes de facturas y boletas
- ❌ **Excel** - No soportado en esta versión con Gemini Vision

## Datos Extraídos

### Boletas
- RUC del emisor
- Razón social del emisor
- Número de boleta
- Fecha de emisión
- Moneda (PEN/USD)
- Montos (subtotal, IGV, total)
- Items detallados

### Facturas
- RUC del emisor y cliente
- Razón social del emisor y cliente
- Número de factura
- Fechas (emisión, vencimiento)
- Moneda (PEN/USD)
- Montos (subtotal, IGV, total)
- Forma de pago
- Items detallados

## Docker (Opcional)

Si prefieres usar Docker:

```bash
# Construir imagen
docker build -t ocr-service .

# Ejecutar contenedor
docker run -p 8080:8080 -v $(pwd)/uploads:/app/uploads --env-file .env ocr-service
```

## Estructura del Proyecto

```
ocr3/
├── app/
│   ├── main.py              # Punto de entrada de la aplicación
│   ├── config.py            # Configuración y variables de entorno
│   ├── db.py                # Conexión a base de datos
│   ├── models.py            # Modelos SQLAlchemy
│   ├── finance_models.py    # Modelos financieros
│   ├── finance_mapper.py    # Mapeo de datos financieros
│   ├── ocr_local.py         # Lógica OCR local
│   ├── ocr_local_excel.py   # Procesamiento OCR para Excel
│   ├── excel_parcel.py      # Procesamiento de parcelas Excel
│   ├── s3_client.py         # Cliente S3
│   ├── textract_client.py   # Cliente Textract
│   └── routers/
│       ├── documents.py     # Rutas de documentos
│       └── ocr.py           # Rutas de OCR
├── scripts/
│   ├── create_schemas.sql   # Script de creación de esquemas
│   ├── create_indexes.sql   # Script de índices
│   └── env.example          # Ejemplo de variables de entorno
├── requirements.txt         # Dependencias Python
├── gunicorn_conf.py         # Configuración Gunicorn
└── Dockerfile               # Configuración Docker
```

## Troubleshooting

### Error de conexión a PostgreSQL
- Verifica que PostgreSQL esté corriendo
- Confirma las credenciales en el archivo `.env`
- Verifica que la base de datos exista

### Error de API Key de Gemini
- Verifica que `GEMINI_API_KEY` esté configurada en tu `.env`
- Asegúrate de que la API Key sea válida
- Revisa los límites de uso en https://makersuite.google.com/

### Error al instalar psycopg2
En Windows, si tienes problemas instalando `psycopg2-binary`:
```bash
pip install psycopg2-binary --no-binary psycopg2-binary
```

### Directorio uploads no encontrado
Asegúrate de crear el directorio:
```bash
mkdir uploads
```

### Error al procesar PDF
Si hay errores con `pdf2image`, instala poppler:
- **Windows**: Descarga de https://github.com/oschwartz10612/poppler-windows/releases/ y agrega al PATH
- **Linux**: `sudo apt-get install poppler-utils`
- **Mac**: `brew install poppler`

### OCR con baja precisión
- Asegúrate de que las imágenes tengan buena calidad (mínimo 300 DPI)
- Los documentos deben estar bien iluminados y sin distorsión
- Para mejores resultados, usa archivos PDF originales en lugar de escaneos

## Licencia

[Especificar licencia]

## Contacto

[Información de contacto]

# Guía de Integración Frontend - OCR Service API

## 📋 Información General

**Base URL**: `http://localhost:9000` (desarrollo) o `https://tu-dominio.com` (producción)

**CORS**: ✅ Habilitado para todos los orígenes en desarrollo

**Formato de respuesta**: JSON

---

## 🔗 Endpoints Disponibles

### 1. Health Check

Verifica que el servicio esté funcionando.

**Endpoint**: `GET /health`

**Respuesta exitosa (200)**:
```json
{
  "ok": true,
  "service": "OCR Service",
  "version": "2.0.0",
  "engine": "Gemini Vision API"
}
```

**Ejemplo JavaScript**:
```javascript
const checkHealth = async () => {
  const response = await fetch('http://localhost:9000/health');
  const data = await response.json();
  console.log(data);
  return data.ok;
};
```

---

### 2. Subir Documento

Sube un archivo (PDF, JPG, PNG) al servidor para procesamiento posterior.

**Endpoint**: `POST /documents/upload`

**Content-Type**: `multipart/form-data`

**Parámetros del formulario**:
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `file` | File | ✅ | Archivo PDF, JPG o PNG |
| `tenant_id` | string | ✅ | UUID del tenant/organización |
| `user_id` | string | ❌ | UUID del usuario (opcional) |
| `doc_kind` | string | ✅ | Tipo: `"boleta"` o `"factura"` |

**Formatos aceptados**:
- `application/pdf`
- `image/jpeg`
- `image/png`

**Tamaño máximo**: 15 MB

**Respuesta exitosa (200)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "storage_key": "tenant_id/doc_id/filename.pdf",
  "message": "Documento subido exitosamente. Use /ocr/process/{doc_id} para procesarlo."
}
```

**Errores comunes**:
- `415`: MIME type no permitido
- `413`: Archivo muy grande (>15MB)
- `422`: Datos de formulario inválidos

**Ejemplo JavaScript (Vanilla)**:
```javascript
const uploadDocument = async (file, tenantId, docKind) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('tenant_id', tenantId);
  formData.append('doc_kind', docKind); // 'boleta' o 'factura'
  
  try {
    const response = await fetch('http://localhost:9000/documents/upload', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('Documento subido:', data);
    return data;
  } catch (error) {
    console.error('Error al subir documento:', error);
    throw error;
  }
};

// Uso con input file
const fileInput = document.getElementById('fileInput');
fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (file) {
    const result = await uploadDocument(
      file,
      'tu-tenant-uuid-aqui',
      'boleta' // o 'factura'
    );
  }
});
```

**Ejemplo React**:
```jsx
import { useState } from 'react';

function DocumentUploader() {
  const [file, setFile] = useState(null);
  const [docKind, setDocKind] = useState('factura');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  const handleUpload = async () => {
    if (!file) return;
    
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('tenant_id', 'your-tenant-uuid');
    formData.append('doc_kind', docKind);

    try {
      const response = await fetch('http://localhost:9000/documents/upload', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      setUploadResult(data);
      console.log('Subida exitosa:', data);
    } catch (error) {
      console.error('Error:', error);
      alert('Error al subir documento');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <select value={docKind} onChange={(e) => setDocKind(e.target.value)}>
        <option value="factura">Factura</option>
        <option value="boleta">Boleta</option>
      </select>
      
      <input 
        type="file" 
        accept=".pdf,.jpg,.jpeg,.png"
        onChange={(e) => setFile(e.target.files[0])}
      />
      
      <button onClick={handleUpload} disabled={!file || uploading}>
        {uploading ? 'Subiendo...' : 'Subir Documento'}
      </button>

      {uploadResult && (
        <div>
          <p>ID: {uploadResult.id}</p>
          <p>{uploadResult.message}</p>
        </div>
      )}
    </div>
  );
}
```

---

### 3. Procesar OCR

Procesa un documento previamente subido usando Gemini Vision API y extrae toda la información estructurada.

**Endpoint**: `POST /ocr/process/{doc_id}`

**Parámetros de ruta**:
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `doc_id` | string (UUID) | ID del documento obtenido al subirlo |

**No requiere body**

**Respuesta exitosa (200)**:
```json
{
  "engine": "gemini-vision",
  "doc_kind": "boleta",
  "invoice_id": "uuid-de-la-invoice",
  "confidence": 0.85,
  "data": {
    "provider": {
      "ruc": "20123456789",
      "razon_social": "MI EMPRESA SAC"
    },
    "invoice": {
      "numero": "B001-00012345",
      "fecha": "2024-11-14",
      "moneda": "PEN",
      "subtotal": "127.12",
      "igv": "22.88",
      "total": "150.00"
    },
    "items": [
      {
        "descripcion": "Producto ejemplo 1",
        "cantidad": "2",
        "precio_unitario": "63.56",
        "total": "127.12"
      },
      {
        "descripcion": "Producto ejemplo 2",
        "cantidad": "1",
        "precio_unitario": "50.00",
        "total": "50.00"
      }
    ]
  },
  "message": "OCR procesado exitosamente. Los datos están listos para enviar al microservicio 'insights'."
}
```

**Estructura de datos - Boleta**:
```typescript
interface BoletaData {
  provider: {
    ruc: string | null;
    razon_social: string | null;
  };
  invoice: {
    numero: string | null;
    fecha: string | null;  // formato: YYYY-MM-DD
    moneda: "PEN" | "USD" | null;
    subtotal?: string | null;
    igv?: string | null;
    total: string | null;
  };
  items: Array<{
    descripcion: string;
    cantidad: string;
    precio_unitario: string;
    total: string;
  }>;
}
```

**Estructura de datos - Factura**:
```typescript
interface FacturaData {
  provider: {
    ruc: string | null;
    razon_social: string | null;
    direccion?: string | null;
  };
  cliente?: {
    ruc: string | null;
    razon_social: string | null;
  };
  invoice: {
    numero: string | null;
    fecha: string | null;  // formato: YYYY-MM-DD
    fecha_vencimiento?: string | null;  // formato: YYYY-MM-DD
    moneda: "PEN" | "USD" | null;
    subtotal: string | null;
    igv: string | null;
    total: string | null;
    forma_pago?: string | null;
  };
  items: Array<{
    descripcion: string;
    cantidad: string;
    precio_unitario: string;
    total: string;
  }>;
}
```

**Errores comunes**:
- `400`: doc_id no es un UUID válido
- `404`: Documento no encontrado
- `422`: Documento sin archivo o Excel no soportado
- `500`: Error en el procesamiento OCR

**Ejemplo JavaScript**:
```javascript
const processOCR = async (docId) => {
  try {
    const response = await fetch(`http://localhost:9000/ocr/process/${docId}`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('OCR procesado:', data);
    return data;
  } catch (error) {
    console.error('Error al procesar OCR:', error);
    throw error;
  }
};
```

**Ejemplo React con estado de carga**:
```jsx
function OCRProcessor({ documentId }) {
  const [processing, setProcessing] = useState(false);
  const [ocrData, setOcrData] = useState(null);
  const [error, setError] = useState(null);

  const processDocument = async () => {
    setProcessing(true);
    setError(null);

    try {
      const response = await fetch(`http://localhost:9000/ocr/process/${documentId}`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('Error al procesar OCR');
      }

      const data = await response.json();
      setOcrData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div>
      <button onClick={processDocument} disabled={processing}>
        {processing ? 'Procesando...' : 'Procesar OCR'}
      </button>

      {error && <div className="error">{error}</div>}

      {ocrData && (
        <div className="results">
          <h3>Resultados OCR</h3>
          <p><strong>Motor:</strong> {ocrData.engine}</p>
          <p><strong>Tipo:</strong> {ocrData.doc_kind}</p>
          <p><strong>Confianza:</strong> {(ocrData.confidence * 100).toFixed(1)}%</p>
          
          <h4>Proveedor</h4>
          <p>RUC: {ocrData.data.provider.ruc}</p>
          <p>Razón Social: {ocrData.data.provider.razon_social}</p>
          
          <h4>Factura/Boleta</h4>
          <p>Número: {ocrData.data.invoice.numero}</p>
          <p>Fecha: {ocrData.data.invoice.fecha}</p>
          <p>Total: {ocrData.data.invoice.moneda} {ocrData.data.invoice.total}</p>
          
          <h4>Items ({ocrData.data.items.length})</h4>
          <ul>
            {ocrData.data.items.map((item, idx) => (
              <li key={idx}>
                {item.descripcion} - Cantidad: {item.cantidad} - Total: {item.total}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

---

## 🔄 Flujo Completo de Integración

### Flujo Básico

```javascript
async function processDocumentComplete(file, tenantId, docKind) {
  try {
    // 1. Subir documento
    console.log('1. Subiendo documento...');
    const uploadResult = await uploadDocument(file, tenantId, docKind);
    const docId = uploadResult.id;
    console.log('✓ Documento subido con ID:', docId);
    
    // 2. Procesar OCR
    console.log('2. Procesando OCR...');
    const ocrResult = await processOCR(docId);
    console.log('✓ OCR completado con confianza:', ocrResult.confidence);
    
    // 3. Ahora puedes enviar los datos a tu microservicio 'insights'
    console.log('3. Enviando a insights...');
    const insightsResult = await sendToInsights(ocrResult.data);
    console.log('✓ Análisis completado');
    
    return {
      documentId: docId,
      ocrData: ocrResult.data,
      insights: insightsResult
    };
    
  } catch (error) {
    console.error('Error en el flujo:', error);
    throw error;
  }
}

// Función para enviar a tu microservicio de insights
async function sendToInsights(ocrData) {
  const response = await fetch('http://tu-servicio-insights/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ocrData: ocrData,
      timestamp: new Date().toISOString()
    })
  });
  
  return await response.json();
}
```

### Componente React Completo

```jsx
import { useState } from 'react';

function CompleteOCRWorkflow() {
  const [file, setFile] = useState(null);
  const [docKind, setDocKind] = useState('factura');
  const [tenantId, setTenantId] = useState('');
  const [status, setStatus] = useState('idle'); // idle, uploading, processing, complete, error
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleProcess = async () => {
    if (!file || !tenantId) {
      alert('Por favor completa todos los campos');
      return;
    }

    try {
      // Paso 1: Subir
      setStatus('uploading');
      const formData = new FormData();
      formData.append('file', file);
      formData.append('tenant_id', tenantId);
      formData.append('doc_kind', docKind);

      const uploadResponse = await fetch('http://localhost:9000/documents/upload', {
        method: 'POST',
        body: formData
      });

      if (!uploadResponse.ok) throw new Error('Error al subir');
      const uploadData = await uploadResponse.json();

      // Paso 2: Procesar OCR
      setStatus('processing');
      const ocrResponse = await fetch(`http://localhost:9000/ocr/process/${uploadData.id}`, {
        method: 'POST'
      });

      if (!ocrResponse.ok) throw new Error('Error al procesar OCR');
      const ocrData = await ocrResponse.json();

      setResult(ocrData);
      setStatus('complete');
      
      // Aquí puedes enviar a insights si lo necesitas
      // await sendToInsights(ocrData.data);

    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  };

  return (
    <div className="ocr-workflow">
      <h2>Procesar Documento</h2>
      
      <div className="form">
        <input
          type="text"
          placeholder="Tenant ID (UUID)"
          value={tenantId}
          onChange={(e) => setTenantId(e.target.value)}
        />

        <select value={docKind} onChange={(e) => setDocKind(e.target.value)}>
          <option value="factura">Factura</option>
          <option value="boleta">Boleta</option>
        </select>

        <input
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={(e) => setFile(e.target.files[0])}
        />

        <button 
          onClick={handleProcess}
          disabled={status === 'uploading' || status === 'processing'}
        >
          {status === 'uploading' && 'Subiendo...'}
          {status === 'processing' && 'Procesando OCR...'}
          {(status === 'idle' || status === 'complete' || status === 'error') && 'Procesar Documento'}
        </button>
      </div>

      {status === 'uploading' && (
        <div className="status">📤 Subiendo documento...</div>
      )}

      {status === 'processing' && (
        <div className="status">🔍 Procesando con Gemini Vision...</div>
      )}

      {status === 'error' && (
        <div className="error">❌ Error: {error}</div>
      )}

      {status === 'complete' && result && (
        <div className="results">
          <h3>✅ Procesamiento Completado</h3>
          <div className="data">
            <p><strong>Tipo:</strong> {result.doc_kind}</p>
            <p><strong>Confianza:</strong> {(result.confidence * 100).toFixed(1)}%</p>
            
            <h4>Datos Extraídos:</h4>
            <pre>{JSON.stringify(result.data, null, 2)}</pre>
            
            <button onClick={() => {
              // Copiar al clipboard
              navigator.clipboard.writeText(JSON.stringify(result.data));
              alert('Datos copiados al portapapeles');
            }}>
              Copiar JSON
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default CompleteOCRWorkflow;
```

---

## 📝 Notas Importantes

### Manejo de Errores

Siempre verifica el status code de las respuestas:

```javascript
const response = await fetch(url, options);

if (!response.ok) {
  const errorData = await response.json();
  console.error('Error del servidor:', errorData);
  throw new Error(errorData.detail || 'Error desconocido');
}
```

### Validación de Archivos en el Frontend

```javascript
function validateFile(file) {
  const validTypes = ['application/pdf', 'image/jpeg', 'image/png'];
  const maxSize = 15 * 1024 * 1024; // 15MB

  if (!validTypes.includes(file.type)) {
    throw new Error('Tipo de archivo no válido. Use PDF, JPG o PNG');
  }

  if (file.size > maxSize) {
    throw new Error('El archivo es muy grande. Máximo 15MB');
  }

  return true;
}
```

### Tiempo de Procesamiento

El procesamiento OCR puede tomar entre 5-15 segundos dependiendo de:
- Tamaño del documento
- Calidad de la imagen
- Cantidad de texto a procesar

**Recomendación**: Muestra un indicador de carga mientras procesas.

### Valores Nulos

La API puede retornar `null` en campos que no se pudieron extraer. Maneja estos casos en tu frontend:

```javascript
const displayValue = (value, defaultText = 'No disponible') => {
  return value || defaultText;
};

// Uso
<p>RUC: {displayValue(data.provider.ruc)}</p>
```

### Calidad de Extracción

Para mejores resultados:
- ✅ Usa documentos originales (PDF) en lugar de escaneos
- ✅ Asegura buena iluminación en fotos
- ✅ Mínimo 300 DPI para escaneos
- ✅ Documentos sin distorsión o manchas

---

## 🔐 Seguridad

### En Producción

1. **CORS**: Cambia `allow_origins=["*"]` a tus dominios específicos
2. **Autenticación**: Agrega tokens JWT o API keys
3. **Rate Limiting**: Implementa límites de peticiones
4. **HTTPS**: Usa siempre conexiones seguras

### Ejemplo con Headers de Autorización

```javascript
const API_KEY = 'tu-api-key-aqui';

const uploadWithAuth = async (file, tenantId, docKind) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('tenant_id', tenantId);
  formData.append('doc_kind', docKind);

  const response = await fetch('https://api.tu-dominio.com/documents/upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`
    },
    body: formData
  });

  return await response.json();
};
```

---

## 🐛 Debugging

### Ver respuesta completa

```javascript
const response = await fetch(url, options);
console.log('Status:', response.status);
console.log('Headers:', [...response.headers.entries()]);

const data = await response.json();
console.log('Data:', data);
```

### Logs del servidor

El servidor registra información útil en consola. Revisa los logs para:
- Errores de procesamiento
- Tiempo de respuesta
- Documentos procesados

---

## 📚 Recursos Adicionales

- **Documentación Interactiva**: http://localhost:9000/docs
- **Health Check**: http://localhost:9000/health
- **Repositorio**: [Tu repo en GitHub]

---

## 💬 Soporte

Si encuentras problemas:
1. Verifica que el servicio esté corriendo: `GET /health`
2. Revisa los logs del servidor
3. Valida el formato de tus peticiones con la documentación interactiva en `/docs`

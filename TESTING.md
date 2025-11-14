# Test del Servicio OCR con Gemini

Este archivo contiene ejemplos de cómo usar el servicio OCR desde tu frontend.

## 1. Subir un documento

```bash
curl -X POST "http://localhost:8080/documents/upload" \
  -F "file=@ruta/a/tu/boleta.pdf" \
  -F "tenant_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "doc_kind=boleta"
```

## 2. Procesar OCR

```bash
curl -X POST "http://localhost:8080/ocr/process/{doc_id}"
```

## 3. Ejemplo en JavaScript (Frontend)

```javascript
// Función para subir documento
async function uploadDocument(file, tenantId, docKind) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('tenant_id', tenantId);
  formData.append('doc_kind', docKind); // 'boleta' o 'factura'
  
  const response = await fetch('http://localhost:8080/documents/upload', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
}

// Función para procesar OCR
async function processOCR(docId) {
  const response = await fetch(`http://localhost:8080/ocr/process/${docId}`, {
    method: 'POST'
  });
  
  return await response.json();
}

// Flujo completo
async function processDocument(file, tenantId, docKind) {
  try {
    // 1. Subir documento
    const uploadResult = await uploadDocument(file, tenantId, docKind);
    console.log('Documento subido:', uploadResult);
    
    // 2. Procesar OCR
    const ocrResult = await processOCR(uploadResult.id);
    console.log('OCR procesado:', ocrResult);
    
    // 3. Enviar a microservicio insights
    const insightsResponse = await fetch('http://tu-servicio-insights/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        documentId: uploadResult.id,
        ocrData: ocrResult.data
      })
    });
    
    return await insightsResponse.json();
    
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}

// Usar en un evento de input file
document.getElementById('fileInput').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  const docKind = document.getElementById('docKind').value; // 'boleta' o 'factura'
  
  const result = await processDocument(
    file, 
    'tenant-uuid-aqui', 
    docKind
  );
  
  console.log('Resultado final:', result);
});
```

## 4. Ejemplo en React

```jsx
import { useState } from 'react';

function DocumentUploader() {
  const [file, setFile] = useState(null);
  const [docKind, setDocKind] = useState('factura');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // 1. Subir documento
      const formData = new FormData();
      formData.append('file', file);
      formData.append('tenant_id', 'your-tenant-id');
      formData.append('doc_kind', docKind);

      const uploadRes = await fetch('http://localhost:8080/documents/upload', {
        method: 'POST',
        body: formData
      });
      const uploadData = await uploadRes.json();

      // 2. Procesar OCR
      const ocrRes = await fetch(`http://localhost:8080/ocr/process/${uploadData.id}`, {
        method: 'POST'
      });
      const ocrData = await ocrRes.json();

      setResult(ocrData);
      
      // 3. Aquí enviarías a tu microservicio insights
      // await sendToInsights(ocrData);
      
    } catch (error) {
      console.error('Error:', error);
      alert('Error procesando documento');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <select value={docKind} onChange={(e) => setDocKind(e.target.value)}>
        <option value="factura">Factura</option>
        <option value="boleta">Boleta</option>
      </select>
      
      <input 
        type="file" 
        accept=".pdf,.jpg,.jpeg,.png"
        onChange={(e) => setFile(e.target.files[0])}
      />
      
      <button type="submit" disabled={!file || loading}>
        {loading ? 'Procesando...' : 'Subir y Procesar'}
      </button>

      {result && (
        <div>
          <h3>Resultado OCR:</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </form>
  );
}
```

## 5. Estructura de Respuesta

```json
{
  "engine": "gemini-vision",
  "doc_kind": "boleta",
  "invoice_id": "uuid-invoice",
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
        "descripcion": "Producto ejemplo",
        "cantidad": "2",
        "precio_unitario": "63.56",
        "total": "127.12"
      }
    ]
  }
}
```

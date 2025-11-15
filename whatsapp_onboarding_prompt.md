# WhatsApp Auto--Onboarding Prompt

## 🧠 **Prompt: Implementación de Auto--Onboarding de Usuario vía WhatsApp para mi plataforma de OCR Financiero**

Quiero que implementes un flujo completo de **auto--onboarding y uso de
mi sistema financiero/contable** vía WhatsApp Business Cloud API. El
objetivo es que el usuario solo envíe un mensaje al WhatsApp y **eso lo
registre, lo identifique y procese automáticamente sus documentos**, sin
necesidad de login manual.

------------------------------------------------------------------------

## ✅ **Objetivo General**

Construir un endpoint `/webhook/whatsapp` que:

1.  **Identifique automáticamente a un usuario por su número de
    WhatsApp.**
2.  **Cree un nuevo tenant/empresa si es la primera vez que escribe.**
3.  **Relacione su número → tenant_id.**
4.  **Permita que simplemente enviando fotos o PDFs, mi OCR procese la
    información.**
5.  **Use Gemini Vision u OCR interno para extraer datos de
    facturas/boletas.**
6.  **Devuelva al usuario un mensaje limpio y formateado en WhatsApp.**

------------------------------------------------------------------------

## 📌 **Reglas del Auto--Onboarding**

Cuando llega un mensaje de un número que no existe en mi BD:

1.  Crear en `auth.tenant`:

    -   `tenant_id`: UUID
    -   `whatsapp_number`
    -   `created_at`

2.  Crear en `auth.users` un usuario tipo "WhatsApp User":

    -   `user_id`
    -   `tenant_id`
    -   `role = "owner"`
    -   `onboarding_step = "complete"`

3.  Guardar relación:

    ``` sql
    phone_number → tenant_id
    ```

4.  Enviar mensaje: \> 👋 ¡Hola! Te acabo de registrar automáticamente.\
    \> Puedes enviarme fotos o PDFs de boletas/facturas y las procesaré
    por ti.

------------------------------------------------------------------------

## 📂 **Estructura requerida en mi backend**

Crear módulo:

    app/
     └── whatsapp/
           ├── router.py
           ├── onboarding.py
           ├── processor.py
           ├── client.py
           └── helpers.py

------------------------------------------------------------------------

## 🔧 **Lógica que debe implementar el endpoint `/webhook/whatsapp`**

1.  Detectar `from_number`.
2.  Llamar:

``` python
tenant = get_or_create_tenant_by_whatsapp(from_number)
```

3.  Si es un mensaje de texto:
    -   Responder instrucciones.
4.  Si es un PDF o una imagen:
    -   Descargar el media

    -   Guardarlo local

    -   Insertar documento en `documents.documents`

    -   Procesarlo con OCR

    -   Insertar resultado en `extractor.extractions`

    -   Formatear mensaje de respuesta

    -   Enviar con:

        ``` python
        send_whatsapp_message(to, text)
        ```

------------------------------------------------------------------------

## 🧠 **Respuesta Formateada**

Quiero respuestas con *Markdown compatible con WhatsApp*:

    💼 *Proveedor*
    RUC: 123456789
    Razón Social: Ejemplo SAC

    📄 *Factura*
    Serie: F001
    Número: 123
    Total: S/ 450.00

    📦 *Items*
    1. Producto 1 - S/ 200
    2. Producto 2 - S/ 250

------------------------------------------------------------------------

## 🧪 **Casos que debes manejar**

-   Usuario nuevo → auto--registro automático.
-   Archivos corruptos → mensaje con error.
-   Archivos que no son PDF/imagen → mensaje de advertencia.
-   Mensaje vacío.
-   Usuario enviando varias imágenes → procesar en orden.
-   Tiempo de espera máximo 30s por OCR.

------------------------------------------------------------------------

## 🔐 **Persistencia requerida**

### `auth.tenants`

  campo             tipo
  ----------------- -------------
  id (UUID)         PK
  whatsapp_number   text
  created_at        timestamptz

### `auth.users`

  campo       tipo
  ----------- -------------------
  id          UUID
  tenant_id   UUID
  source      text ("whatsapp")
  phone       text

### `documents.documents`

Debe guardar PDF/imagen asociado al tenant.

### `extractor.extractions`

Guardar la salida del OCR.

------------------------------------------------------------------------

## 📌 **Comportamiento esperado en WhatsApp**

**Usuario:** "Hola"

**Bot:**\
\> 👋 ¡Hola! Te acabo de registrar automáticamente.\
\> Envíame una foto o PDF de tu boleta/factura y la analizaré por ti.

------------------------------------------------------------------------

## 🚀 **Entrega final que espero**

### 1. Código backend funcional

-   `/webhook/whatsapp`
-   Auto--onboarding
-   OCR con Gemini
-   Respuestas formateadas
-   Guardado en documentos + extracciones

### 2. Manejo de errores

### 3. Logs limpios

------------------------------------------------------------------------

## 👍 **Fin del Prompt**

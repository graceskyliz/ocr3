# Dockerfile para OCR3 FastAPI + Gemini + WhatsApp
FROM python:3.12-slim

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpoppler-cpp-dev \
        poppler-utils \
        tesseract-ocr \
        libtesseract-dev \
        libleptonica-dev \
        gcc \
        git \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements y archivos fuente
COPY requirements.txt ./

# Instalar dependencias de Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código fuente
COPY . .

# Crear carpeta de uploads
RUN mkdir -p /app/uploads

# Variables de entorno (puedes sobreescribir en docker-compose o al correr)
ENV PYTHONUNBUFFERED=1 \
    UPLOAD_DIR=/app/uploads \
    MAX_UPLOAD_MB=15

# Exponer el puerto de la API
EXPOSE 9000

# Comando para correr el servidor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]

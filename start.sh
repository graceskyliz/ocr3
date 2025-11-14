#!/bin/bash
# Script para iniciar el servicio OCR en Linux/Mac

echo "================================"
echo "OCR Service con Gemini Vision"
echo "================================"
echo ""

# Verificar que existe .env
if [ ! -f .env ]; then
    echo "ERROR: No se encontró el archivo .env"
    echo "Por favor crea un archivo .env con tu GEMINI_API_KEY"
    exit 1
fi

# Verificar que existe el directorio uploads
if [ ! -d uploads ]; then
    echo "Creando directorio uploads..."
    mkdir uploads
fi

echo "Iniciando servidor..."
echo "Accede a: http://localhost:8080/docs"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

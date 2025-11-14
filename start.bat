@echo off
REM Script para iniciar el servicio OCR

echo ================================
echo OCR Service con Gemini Vision
echo ================================
echo.

REM Verificar que existe .env
if not exist .env (
    echo ERROR: No se encontro el archivo .env
    echo Por favor crea un archivo .env con tu GEMINI_API_KEY
    pause
    exit /b 1
)

REM Verificar que existe el directorio uploads
if not exist uploads (
    echo Creando directorio uploads...
    mkdir uploads
)

echo Iniciando servidor...
echo Accede a: http://localhost:8080/docs
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# app/settings.py
import os
from urllib.parse import quote_plus

class Settings:
    # Database
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT") or "5432"
    DB_NAME = os.getenv("DB_NAME")

    # opcional: permitir DB_URL directa si ya viene definida
    DB_URL = os.getenv("DB_URL")
    if not DB_URL:
        if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
            raise RuntimeError("Variables DB_USER, DB_PASSWORD, DB_HOST, DB_NAME son requeridas")
        DB_URL = (
            f"postgresql+psycopg2://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}"
            f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

    # Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY es requerida")
    
    # Storage local
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "15"))
    ALLOWED_MIME = set((os.getenv("ALLOWED_MIME") or
                        "application/pdf,image/jpeg,image/png,"
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet").split(","))
    
    # WhatsApp Cloud API
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
    PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")
    APP_VERIFY_TOKEN = os.getenv("APP_VERIFY_TOKEN", "thesaurus-whatsapp")

settings = Settings()

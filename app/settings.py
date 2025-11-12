# app/settings.py
import os
from urllib.parse import quote_plus

class Settings:
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

    S3_BUCKET = os.getenv("S3_BUCKET")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

settings = Settings()

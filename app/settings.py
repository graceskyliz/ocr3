# app/settings.py
import os

class Settings:
    # Lee del entorno; falla explícito si falta el bucket
    INGEST_BUCKET: str | None = os.getenv("INGEST_BUCKET")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")

settings = Settings()

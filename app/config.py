import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    APP_ENV = os.getenv("APP_ENV", "dev")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

    # S3
    S3_BUCKET = os.getenv("S3_BUCKET")
    S3_PREFIX = os.getenv("S3_PREFIX", "uploads/")

    # DB
    DB_URL = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )

    # Seguridad / archivos
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "15"))
    ALLOWED_MIME = set((os.getenv("ALLOWED_MIME") or
                        "application/pdf,image/jpeg,image/png,"
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet").split(","))

settings = Settings()

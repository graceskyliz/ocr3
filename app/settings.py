import os
class Settings:
    S3_BUCKET = os.getenv("S3_BUCKET")            # ← usa el nombre real
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
settings = Settings()

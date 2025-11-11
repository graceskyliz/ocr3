import boto3, hashlib
from .config import settings

s3 = boto3.client("s3", region_name=settings.AWS_REGION)

def put_file(fp, key):
    s3.upload_fileobj(fp, settings.S3_BUCKET, key, ExtraArgs={"ServerSideEncryption": "AES256"})
    return f"s3://{settings.S3_BUCKET}/{key}"

def get_object_bytes(key) -> bytes:
    obj = s3.get_object(Bucket=settings.S3_BUCKET, Key=key)
    return obj["Body"].read()

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

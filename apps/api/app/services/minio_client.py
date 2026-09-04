from minio import Minio
from minio.error import S3Error
from app.core.config import settings

def get_minio_client():
    client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )
    
    bucket_name = "geoscope"
    try:
        found = client.bucket_exists(bucket_name)
        if not found:
            client.make_bucket(bucket_name)
    except Exception as e:
        print(f"Error checking or creating MinIO bucket: {e}")
        
    return client

minio_client = get_minio_client()

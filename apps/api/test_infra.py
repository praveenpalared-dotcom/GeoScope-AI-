import os
from dotenv import load_dotenv
import psycopg2
from minio import Minio

# Load environment variables
load_dotenv()

print("Testing Infrastructure Connections...\n")

# 1. Test PostgreSQL Connection
try:
    print("Testing PostgreSQL connection...")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not found in .env")
        
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    print(f"✅ Successfully connected to PostgreSQL!")
    print(f"   Version: {db_version[0]}\n")
    conn.close()
except Exception as e:
    print(f"❌ PostgreSQL connection failed: {e}\n")

# 2. Test MinIO Connection
try:
    print("Testing MinIO connection...")
    minio_endpoint = os.getenv("MINIO_ENDPOINT")
    minio_access_key = os.getenv("MINIO_ACCESS_KEY")
    minio_secret_key = os.getenv("MINIO_SECRET_KEY")
    minio_use_ssl = os.getenv("MINIO_USE_SSL", "false").lower() == "true"
    
    if not all([minio_endpoint, minio_access_key, minio_secret_key]):
        raise ValueError("Missing MinIO configuration in .env")

    client = Minio(
        minio_endpoint,
        access_key=minio_access_key,
        secret_key=minio_secret_key,
        secure=minio_use_ssl
    )
    
    buckets = client.list_buckets()
    print(f"✅ Successfully connected to MinIO!")
    print(f"   Total buckets found: {len(buckets)}")
    for bucket in buckets:
        print(f"   - {bucket.name}")
        
except Exception as e:
    print(f"❌ MinIO connection failed: {e}\n")

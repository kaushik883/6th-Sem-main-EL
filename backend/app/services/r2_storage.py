import boto3
from botocore.config import Config
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=Config(signature_version='s3v4'),
    )

async def upload_file_to_r2(file_path: str, object_name: str) -> str:
    """
    Uploads a local file to Cloudflare R2 and returns the public URL.
    """
    import asyncio
    
    s3 = get_s3_client()
    
    def upload():
        s3.upload_file(
            file_path,
            settings.R2_BUCKET_NAME,
            object_name,
            ExtraArgs={'ContentType': 'application/pdf'}
        )
        
    try:
        await asyncio.to_thread(upload)
        # Construct public URL
        # We strip trailing slash from R2_PUBLIC_URL if present, and ensure object_name doesn't have a leading slash
        public_base = settings.R2_PUBLIC_URL.rstrip('/')
        obj_key = object_name.lstrip('/')
        return f"{public_base}/{obj_key}"
    except Exception as e:
        logger.error(f"Failed to upload to R2: {str(e)}")
        raise e

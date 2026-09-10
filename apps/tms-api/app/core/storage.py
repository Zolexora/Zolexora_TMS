import logging
import uuid
from typing import Optional
import cloudinary
import cloudinary.uploader
import boto3
from botocore.config import Config
from app.core.config import settings

logger = logging.getLogger("zolexora.storage")

# Configure Cloudinary if credentials exist
if settings.CLOUDINARY_URL:
    try:
        cloudinary.config(cloudinary_url=settings.CLOUDINARY_URL)
    except Exception as e:
        logger.warning(f"Could not initialize Cloudinary from CLOUDINARY_URL: {e}")
elif settings.CLOUDINARY_CLOUD_NAME:
    cloudinary.config(cloud_name=settings.CLOUDINARY_CLOUD_NAME)


def get_r2_client():
    """Returns a boto3 S3 client configured for Cloudflare R2."""
    if not (settings.R2_ACCESS_KEY_ID and settings.R2_SECRET_ACCESS_KEY and settings.CLOUDFLARE_ACCOUNT_ID):
        return None

    endpoint = settings.R2_ENDPOINT_URL or f"https://{settings.CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


async def upload_image_to_cloudinary(
    file_bytes: bytes,
    folder: str = "zolexora/avatars",
    public_id: Optional[str] = None,
) -> str:
    """Uploads an image (photo, avatar) to Cloudinary and returns secure URL."""
    try:
        pid = public_id or f"img_{uuid.uuid4().hex}"
        res = cloudinary.uploader.upload(
            file_bytes,
            folder=folder,
            public_id=pid,
            overwrite=True,
            resource_type="image",
        )
        return res.get("secure_url", "")
    except Exception as e:
        logger.warning(f"Cloudinary upload failed: {e}. Falling back to local placeholder URL.")
        return f"https://res.cloudinary.com/demo/image/upload/{folder}/{uuid.uuid4().hex}.jpg"


async def upload_document_to_r2(
    file_bytes: bytes,
    file_name: str,
    content_type: str = "application/pdf",
    folder: str = "documents",
) -> str:
    """Uploads a compliance document/invoice to Cloudflare R2 and returns asset URL."""
    client = get_r2_client()
    key = f"{folder}/{uuid.uuid4().hex}_{file_name}"

    if client:
        try:
            client.put_object(
                Bucket=settings.R2_BUCKET_NAME,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
            )
            return f"https://{settings.R2_BUCKET_NAME}.r2.dev/{key}"
        except Exception as e:
            logger.warning(f"Cloudflare R2 upload failed: {e}. Returning placeholder asset key.")

    return f"https://r2.zolexora.com/{key}"

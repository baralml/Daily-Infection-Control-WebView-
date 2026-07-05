from celery import Celery
from app.core.config import settings

# Initialize Celery app
celery = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery.task(name="compress_image_async")
def compress_image_async(file_bytes_hex: str, file_name: str, mime_type: str):
    """Asynchronously runs image compression and uploads it to S3."""
    # Convert hex string back to bytes
    file_bytes = bytes.fromhex(file_bytes_hex)
    from app.services.storage import process_and_store_media
    original, compressed, thumbnail = process_and_store_media(file_bytes, file_name, mime_type)
    return {
        "original_url": original,
        "compressed_url": compressed,
        "thumbnail_url": thumbnail
    }

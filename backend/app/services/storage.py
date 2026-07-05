import io
import uuid
from typing import Optional, Tuple
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from PIL import Image

from app.core.config import settings

# Initialize S3 client for MinIO / AWS S3 compatibility
endpoint_url = settings.MINIO_ENDPOINT
if not endpoint_url.startswith("http://") and not endpoint_url.startswith("https://"):
    prefix = "https://" if settings.MINIO_SECURE else "http://"
    endpoint_url = f"{prefix}{endpoint_url}"

s3_client = boto3.client(
    "s3",
    endpoint_url=endpoint_url,
    aws_access_key_id=settings.MINIO_ACCESS_KEY,
    aws_secret_access_key=settings.MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1"
)

def ensure_bucket_exists():
    """Verifies existence of bucket and creates it if missing."""
    try:
        s3_client.head_bucket(Bucket=settings.MINIO_BUCKET_NAME)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            s3_client.create_bucket(Bucket=settings.MINIO_BUCKET_NAME)
            # Set public read policy for media retrieval in dev
            bucket_policy = f"""{{
                "Version": "2012-10-17",
                "Statement": [
                    {{
                        "Sid": "PublicRead",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": ["s3:GetObject"],
                        "Resource": ["arn:aws:s3:::{settings.MINIO_BUCKET_NAME}/*"]
                    }}
                ]
            }}"""
            s3_client.put_bucket_policy(Bucket=settings.MINIO_BUCKET_NAME, Policy=bucket_policy)

def upload_file_to_s3(file_bytes: bytes, file_name: str, content_type: str) -> str:
    """Uploads a raw byte array to S3 and returns the public access URL."""
    ensure_bucket_exists()
    
    s3_client.put_object(
        Bucket=settings.MINIO_BUCKET_NAME,
        Key=file_name,
        Body=file_bytes,
        ContentType=content_type
    )
    
    # Construct access URL
    if settings.MINIO_SECURE:
        base_url = f"https://{settings.MINIO_ENDPOINT}"
    else:
        # In development docker-compose context, external clients access MinIO via localhost:9000
        # backend references minio:9000. We map endpoints appropriately for external fetches.
        endpoint = settings.MINIO_ENDPOINT
        if "minio:9000" in endpoint:
            endpoint = endpoint.replace("minio:9000", "localhost:9000")
        base_url = f"http://{endpoint}"
        
    return f"{base_url}/{settings.MINIO_BUCKET_NAME}/{file_name}"

def compress_image_and_thumbnail(image_bytes: bytes) -> Tuple[bytes, bytes]:
    """Compresses the original image (Max 1200px width/height) 
    and generates a square thumbnail (250x250px). Strips EXIF metadata.
    """
    img = Image.open(io.BytesIO(image_bytes))
    
    # Convert RGBA/P to RGB (JPEG standard)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
        
    # Compress Main Image
    max_size = (1200, 1200)
    img_compressed = img.copy()
    img_compressed.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    compressed_io = io.BytesIO()
    img_compressed.save(compressed_io, format="JPEG", quality=75, optimize=True)
    compressed_bytes = compressed_io.getvalue()
    
    # Generate Thumbnail (Centered crop 250x250)
    thumb_size = 250
    # Determine crop box
    w, h = img.size
    min_dim = min(w, h)
    left = (w - min_dim) / 2
    top = (h - min_dim) / 2
    right = (w + min_dim) / 2
    bottom = (h + min_dim) / 2
    
    img_thumb = img.crop((left, top, right, bottom))
    img_thumb = img_thumb.resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
    
    thumb_io = io.BytesIO()
    img_thumb.save(thumb_io, format="JPEG", quality=70, optimize=True)
    thumb_bytes = thumb_io.getvalue()
    
    return compressed_bytes, thumb_bytes

def process_and_store_media(file_bytes: bytes, file_name: str, mime_type: str) -> Tuple[str, str, str]:
    """Handles storage flow. If image, compresses it, generates a thumbnail,
    stores all three (original, compressed, thumbnail) on MinIO, and returns URLs.
    """
    ext = file_name.split(".")[-1]
    unique_prefix = uuid.uuid4().hex
    
    original_key = f"original/{unique_prefix}_{file_name}"
    compressed_key = f"compressed/{unique_prefix}.jpg"
    thumbnail_key = f"thumbnail/{unique_prefix}.jpg"
    
    original_url = upload_file_to_s3(file_bytes, original_key, mime_type)
    
    if mime_type.startswith("image/"):
        try:
            compressed_bytes, thumb_bytes = compress_image_and_thumbnail(file_bytes)
            compressed_url = upload_file_to_s3(compressed_bytes, compressed_key, "image/jpeg")
            thumbnail_url = upload_file_to_s3(thumb_bytes, thumbnail_key, "image/jpeg")
        except Exception:
            # Fallback to original if image processing fails
            compressed_url = original_url
            thumbnail_url = original_url
    else:
        # Non-image files (audio/video) do not get compressed
        compressed_url = original_url
        thumbnail_url = original_url
        
    return original_url, compressed_url, thumbnail_url

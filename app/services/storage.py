"""
Storage service for handling video uploads, processing, and serving
Supports local storage and cloud storage (AWS S3, Google Cloud)
"""

import os
import uuid
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
from google.cloud import storage as gcs
from fastapi import UploadFile, HTTPException
import ffmpeg
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Unified storage service supporting local and cloud storage"""

    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE  # 'local', 's3', or 'gcs'
        self.local_storage_path = Path(settings.LOCAL_STORAGE_PATH)
        self.max_file_size = settings.MAX_FILE_SIZE  # in bytes
        self.allowed_video_types = settings.ALLOWED_VIDEO_TYPES

        # Initialize cloud storage clients
        self.s3_client = None
        self.gcs_client = None

        if self.storage_type == "s3":
            self._init_s3()
        elif self.storage_type == "gcs":
            self._init_gcs()
        else:
            self._init_local()

    def _init_local(self):
        """Initialize local storage"""
        self.local_storage_path.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.local_storage_path / "videos").mkdir(exist_ok=True)
        (self.local_storage_path / "thumbnails").mkdir(exist_ok=True)
        (self.local_storage_path / "temp").mkdir(exist_ok=True)

        logger.info(f"Local storage initialized at: {self.local_storage_path}")

    def _init_s3(self):
        """Initialize S3 storage"""
        try:
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )

            # Test connection
            self.s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
            logger.info(f"S3 storage initialized: {settings.S3_BUCKET_NAME}")

        except ClientError as e:
            logger.error(f"S3 initialization failed: {e}")
            raise HTTPException(status_code=500, detail="Storage service unavailable")

    def _init_gcs(self):
        """Initialize Google Cloud Storage"""
        try:
            self.gcs_client = gcs.Client(
                project=settings.GCP_PROJECT_ID,
                credentials_path=settings.GCP_CREDENTIALS_PATH,
            )

            # Test connection
            bucket = self.gcs_client.bucket(settings.GCS_BUCKET_NAME)
            bucket.reload()
            logger.info(f"GCS storage initialized: {settings.GCS_BUCKET_NAME}")

        except Exception as e:
            logger.error(f"GCS initialization failed: {e}")
            raise HTTPException(status_code=500, detail="Storage service unavailable")

    async def upload_video(
        self, file: UploadFile, user_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload and process video file"""

        # Validate file
        await self._validate_video_file(file)

        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = self._get_file_extension(file.filename)
        filename = f"{file_id}{file_extension}"

        try:
            # Read file content
            content = await file.read()

            # Calculate file hash for deduplication
            file_hash = hashlib.sha256(content).hexdigest()

            # Check for existing file with same hash
            existing_file = await self._check_duplicate(file_hash, user_id)
            if existing_file:
                logger.info(f"Duplicate file detected: {file_hash}")
                return existing_file

            # Store file based on storage type
            if self.storage_type == "local":
                file_path = await self._store_local(content, filename, user_id)
            elif self.storage_type == "s3":
                file_path = await self._store_s3(content, filename, user_id)
            elif self.storage_type == "gcs":
                file_path = await self._store_gcs(content, filename, user_id)
            else:
                raise HTTPException(
                    status_code=500, detail="Invalid storage configuration"
                )

            # Get video metadata
            video_info = await self._get_video_info(content)

            # Generate thumbnail
            thumbnail_path = await self._generate_thumbnail(content, file_id, user_id)

            # Prepare response
            result = {
                "file_id": file_id,
                "filename": file.filename,
                "file_path": file_path,
                "file_hash": file_hash,
                "file_size": len(content),
                "content_type": file.content_type,
                "thumbnail_path": thumbnail_path,
                "duration": video_info.get("duration"),
                "width": video_info.get("width"),
                "height": video_info.get("height"),
                "fps": video_info.get("fps"),
                "upload_timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "metadata": metadata or {},
            }

            logger.info(f"Video uploaded successfully: {file_id}")
            return result

        except Exception as e:
            logger.error(f"Video upload failed: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    async def _validate_video_file(self, file: UploadFile):
        """Validate uploaded video file"""

        # Check file size
        if hasattr(file.file, "seek"):
            file.file.seek(0, 2)  # Seek to end
            size = file.file.tell()
            file.file.seek(0)  # Reset to beginning

            if size > self.max_file_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB",
                )

        # Check content type
        if file.content_type not in self.allowed_video_types:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid file type. Allowed types: {', '.join(self.allowed_video_types)}",
            )

        # Check file extension
        if not file.filename:
            raise HTTPException(status_code=422, detail="Filename is required")

        extension = self._get_file_extension(file.filename).lower()
        allowed_extensions = [".mp4", ".webm", ".mov", ".avi"]

        if extension not in allowed_extensions:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}",
            )

    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename"""
        return Path(filename).suffix.lower()

    async def _store_local(self, content: bytes, filename: str, user_id: str) -> str:
        """Store file in local storage"""
        user_dir = self.local_storage_path / "videos" / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        file_path = user_dir / filename

        with open(file_path, "wb") as f:
            f.write(content)

        return str(file_path.relative_to(self.local_storage_path))

    async def _store_s3(self, content: bytes, filename: str, user_id: str) -> str:
        """Store file in S3"""
        key = f"videos/{user_id}/{filename}"

        try:
            self.s3_client.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=key,
                Body=content,
                ContentType="video/webm",
                Metadata={
                    "user_id": user_id,
                    "upload_timestamp": datetime.utcnow().isoformat(),
                },
            )

            return f"s3://{settings.S3_BUCKET_NAME}/{key}"

        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise HTTPException(status_code=500, detail="S3 upload failed")

    async def _store_gcs(self, content: bytes, filename: str, user_id: str) -> str:
        """Store file in Google Cloud Storage"""
        blob_name = f"videos/{user_id}/{filename}"

        try:
            bucket = self.gcs_client.bucket(settings.GCS_BUCKET_NAME)
            blob = bucket.blob(blob_name)

            blob.upload_from_string(content, content_type="video/webm")

            # Set metadata
            blob.metadata = {
                "user_id": user_id,
                "upload_timestamp": datetime.utcnow().isoformat(),
            }
            blob.patch()

            return f"gs://{settings.GCS_BUCKET_NAME}/{blob_name}"

        except Exception as e:
            logger.error(f"GCS upload failed: {e}")
            raise HTTPException(status_code=500, detail="GCS upload failed")

    async def _get_video_info(self, content: bytes) -> Dict[str, Any]:
        """Extract video metadata using ffmpeg"""
        try:
            # Save content to temporary file
            temp_path = self.local_storage_path / "temp" / f"{uuid.uuid4()}.webm"
            temp_path.parent.mkdir(parents=True, exist_ok=True)

            with open(temp_path, "wb") as f:
                f.write(content)

            # Use ffprobe to get video info
            probe = ffmpeg.probe(str(temp_path))
            video_stream = next(
                s for s in probe["streams"] if s["codec_type"] == "video"
            )

            info = {
                "duration": float(probe["format"]["duration"]),
                "width": int(video_stream["width"]),
                "height": int(video_stream["height"]),
                "fps": eval(video_stream["r_frame_rate"]),  # Convert fraction to float
                "codec": video_stream["codec_name"],
                "bitrate": int(probe["format"].get("bit_rate", 0)),
            }

            # Cleanup temp file
            temp_path.unlink()

            return info

        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return {}

    async def _generate_thumbnail(
        self, content: bytes, file_id: str, user_id: str
    ) -> Optional[str]:
        """Generate video thumbnail"""
        try:
            # Save content to temporary file
            temp_video_path = self.local_storage_path / "temp" / f"{file_id}.webm"
            temp_thumb_path = self.local_storage_path / "temp" / f"{file_id}_thumb.jpg"

            temp_video_path.parent.mkdir(parents=True, exist_ok=True)

            with open(temp_video_path, "wb") as f:
                f.write(content)

            # Generate thumbnail at 1 second mark
            (
                ffmpeg.input(str(temp_video_path), ss=1)
                .output(
                    str(temp_thumb_path), vframes=1, format="image2", vcodec="mjpeg"
                )
                .overwrite_output()
                .run(quiet=True)
            )

            # Read thumbnail content
            with open(temp_thumb_path, "rb") as f:
                thumb_content = f.read()

            # Store thumbnail
            thumb_filename = f"{file_id}_thumb.jpg"

            if self.storage_type == "local":
                thumb_path = await self._store_thumbnail_local(
                    thumb_content, thumb_filename, user_id
                )
            elif self.storage_type == "s3":
                thumb_path = await self._store_thumbnail_s3(
                    thumb_content, thumb_filename, user_id
                )
            elif self.storage_type == "gcs":
                thumb_path = await self._store_thumbnail_gcs(
                    thumb_content, thumb_filename, user_id
                )
            else:
                thumb_path = None

            # Cleanup temp files
            temp_video_path.unlink()
            temp_thumb_path.unlink()

            return thumb_path

        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            return None

    async def _store_thumbnail_local(
        self, content: bytes, filename: str, user_id: str
    ) -> str:
        """Store thumbnail in local storage"""
        user_dir = self.local_storage_path / "thumbnails" / user_id
        user_dir.mkdir(parents=True, exist_ok=True)

        file_path = user_dir / filename

        with open(file_path, "wb") as f:
            f.write(content)

        return str(file_path.relative_to(self.local_storage_path))

    async def _store_thumbnail_s3(
        self, content: bytes, filename: str, user_id: str
    ) -> str:
        """Store thumbnail in S3"""
        key = f"thumbnails/{user_id}/{filename}"

        self.s3_client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=content,
            ContentType="image/jpeg",
        )

        return f"s3://{settings.S3_BUCKET_NAME}/{key}"

    async def _store_thumbnail_gcs(
        self, content: bytes, filename: str, user_id: str
    ) -> str:
        """Store thumbnail in GCS"""
        blob_name = f"thumbnails/{user_id}/{filename}"

        bucket = self.gcs_client.bucket(settings.GCS_BUCKET_NAME)
        blob = bucket.blob(blob_name)

        blob.upload_from_string(content, content_type="image/jpeg")

        return f"gs://{settings.GCS_BUCKET_NAME}/{blob_name}"

    async def _check_duplicate(
        self, file_hash: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Check for duplicate files (implement with database)"""
        # TODO: Implement database lookup for duplicate files
        # This would check if a file with the same hash already exists for the user
        return None

    def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Generate access URL for file"""

        if self.storage_type == "local":
            # For local storage, return a URL that your web server can serve
            return f"{settings.BASE_URL}/files/{file_path}"

        elif self.storage_type == "s3":
            # Generate presigned URL for S3
            key = file_path.replace(f"s3://{settings.S3_BUCKET_NAME}/", "")
            return self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.S3_BUCKET_NAME, "Key": key},
                ExpiresIn=expires_in,
            )

        elif self.storage_type == "gcs":
            # Generate signed URL for GCS
            blob_name = file_path.replace(f"gs://{settings.GCS_BUCKET_NAME}/", "")
            bucket = self.gcs_client.bucket(settings.GCS_BUCKET_NAME)
            blob = bucket.blob(blob_name)

            return blob.generate_signed_url(
                expiration=datetime.utcnow() + timedelta(seconds=expires_in),
                method="GET",
            )

        return file_path

    async def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        try:
            if self.storage_type == "local":
                full_path = self.local_storage_path / file_path
                if full_path.exists():
                    full_path.unlink()

            elif self.storage_type == "s3":
                key = file_path.replace(f"s3://{settings.S3_BUCKET_NAME}/", "")
                self.s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)

            elif self.storage_type == "gcs":
                blob_name = file_path.replace(f"gs://{settings.GCS_BUCKET_NAME}/", "")
                bucket = self.gcs_client.bucket(settings.GCS_BUCKET_NAME)
                blob = bucket.blob(blob_name)
                blob.delete()

            return True

        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            return False


# Create singleton instance
storage_service = StorageService()

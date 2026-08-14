from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ObjectStorage(Protocol):
    def put(self, local_path: Path, object_key: str, content_type: str) -> str: ...


class S3CompatibleStorage:
    """Lazy S3-compatible adapter; install boto3 in the production image when selected."""

    def __init__(self, endpoint_url: str, bucket: str, access_key: str, secret_key: str) -> None:
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("Install boto3 to enable STORAGE_PROVIDER=s3") from exc
        self.bucket = bucket
        self.endpoint_url = endpoint_url.rstrip("/")
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def put(self, local_path: Path, object_key: str, content_type: str) -> str:
        self.client.upload_file(
            str(local_path),
            self.bucket,
            object_key,
            ExtraArgs={"ContentType": content_type},
        )
        return f"{self.endpoint_url}/{self.bucket}/{object_key}"

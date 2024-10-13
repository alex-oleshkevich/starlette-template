import dataclasses
import os

from async_storages import FileSystemBackend, MemoryBackend, S3Backend

from app.config import settings
from app.contrib.storage import FileStorage, StorageType

__all__ = ["file_storage"]


@dataclasses.dataclass
class StorageConfig:
    type: StorageType
    local_dir: str | os.PathLike[str] | None = None
    local_url_prefix: str | None = None
    s3_bucket: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_region: str | None = None
    s3_endpoint: str | None = None


def file_storage_factory(settings: StorageConfig) -> FileStorage:
    if settings.type == StorageType.S3:
        assert settings.s3_bucket
        assert settings.s3_access_key
        assert settings.s3_secret_key
        return FileStorage(
            S3Backend(
                bucket=settings.s3_bucket,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region,
                endpoint_url=settings.s3_endpoint,
                signed_link_ttl=3600,
            )
        )
    if settings.type == StorageType.LOCAL:
        assert settings.local_dir
        assert settings.local_url_prefix
        return FileStorage(
            FileSystemBackend(
                mkdirs=False,
                mkdir_exists_ok=True,
                mkdir_permissions=0o777,
                base_dir=settings.local_dir,
                base_url=settings.local_url_prefix,
            )
        )
    return FileStorage(MemoryBackend())


file_storage = file_storage_factory(
    StorageConfig(
        type=settings.storages_type,
        local_dir=settings.storages_local_dir,
        local_url_prefix=settings.storages_local_url_prefix,
        s3_bucket=settings.storages_s3_bucket,
        s3_access_key=settings.storages_s3_access_key,
        s3_secret_key=settings.storages_s3_secret_key,
        s3_region=settings.storages_s3_region,
        s3_endpoint=settings.storages_s3_endpoint,
    )
)

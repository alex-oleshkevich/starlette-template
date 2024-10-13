import pytest

from app.config.files import StorageConfig, file_storage_factory
from app.contrib.storage import StorageType


@pytest.mark.parametrize(
    "config",
    [
        StorageConfig(
            type=StorageType.LOCAL,
            local_dir="local_dir",
            local_url_prefix="local_url_prefix",
        ),
        StorageConfig(
            type=StorageType.S3,
            s3_bucket="s3_bucket",
            s3_access_key="s3_access_key",
            s3_secret_key="s3_secret_key",
            s3_region="s3_region",
            s3_endpoint="s3_endpoint",
        ),
        StorageConfig(
            type=StorageType.MEMORY,
        ),
    ],
)
def test_file_storage_factory(config: StorageConfig) -> None:
    storage = file_storage_factory(config)
    assert storage

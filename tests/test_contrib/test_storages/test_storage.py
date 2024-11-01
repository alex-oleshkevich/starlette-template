import io

from async_storages import MemoryBackend
from starlette.datastructures import UploadFile

from app.contrib.storage import FileStorage


async def test_upload() -> None:
    storage = FileStorage(storage=MemoryBackend())
    file_path = await storage.upload(
        extra_tokens={},
        destination="files/{file_name}",
        upload_file=UploadFile(file=io.BytesIO(b"test"), filename="test.txt"),
    )
    assert file_path == "files/test.txt"


async def test_upload_many() -> None:
    storage = FileStorage(storage=MemoryBackend())
    file_paths = await storage.upload_many(
        [
            UploadFile(file=io.BytesIO(b"test"), filename="test.txt"),
            UploadFile(file=io.BytesIO(b"test"), filename="test2.txt"),
        ],
        destination="files/{file_name}",
        extra_tokens={},
    )
    assert sorted(file_paths) == sorted(["files/test.txt", "files/test2.txt"])


async def test_delete_many() -> None:
    backend = MemoryBackend()
    storage = FileStorage(storage=backend)
    await storage.write("test.txt", io.BytesIO(b"test"))
    await storage.write("test2.txt", io.BytesIO(b"test"))

    await storage.delete_many(["test.txt", "test2.txt"])
    assert not await backend.exists("test.txt")
    assert not await backend.exists("test2.txt")

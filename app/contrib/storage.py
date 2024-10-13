import enum
import typing

import anyio
from async_storages import FileStorage as BaseFileStore
from async_storages import generate_file_path
from starlette.datastructures import UploadFile


class StorageType(enum.StrEnum):
    LOCAL = "local"
    MEMORY = "memory"
    S3 = "s3"


class FileStorage(BaseFileStore):
    async def upload(
        self, upload_file: UploadFile, destination: str, *, extra_tokens: typing.Mapping[str, typing.Any] | None = None
    ) -> str:
        assert upload_file.filename, "Filename is required"
        file_name = generate_file_path(upload_file.filename, destination, extra_tokens=extra_tokens or {})
        await self.storage.write(file_name, upload_file)
        return file_name

    async def upload_many(
        self,
        files: typing.Sequence[UploadFile],
        destination: str,
        *,
        extra_tokens: typing.Mapping[str, typing.Any] | None = None,
    ) -> list[str]:
        file_names: list[str] = []
        extra_tokens = extra_tokens or {}

        async def worker(file: UploadFile) -> None:
            assert file.filename, "Filename is required"
            file_path = await self.upload(file, destination, extra_tokens=extra_tokens)
            file_names.append(file_path)

        async with anyio.create_task_group() as tg:
            for file in files:
                tg.start_soon(worker, file)
        return file_names

    async def delete_many(self, file_names: typing.Sequence[str]) -> None:
        async with anyio.create_task_group() as tg:
            for file_name in file_names:
                tg.start_soon(self.delete, file_name)

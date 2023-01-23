from typing import Dict, List, Optional, Union

from pctasks.core.models.base import PCBaseModel
from pctasks.core.models.config import CodeConfig
from pctasks.core.models.task import TaskDefinition
from pctasks.dataset.chunks.constants import (
    ASSET_CHUNKS_PREFIX,
    CREATE_CHUNKS_TASK_PATH,
    LIST_CHUNKS_TASK_PATH,
)
from pctasks.dataset.constants import CREATE_CHUNKS_TASK_ID, LIST_CHUNKS_TASK_ID
from pctasks.dataset.models import ChunkOptions, CollectionDefinition, DatasetDefinition


class CreateChunksInput(PCBaseModel):
    src_uri: str
    """Storage URI for the source assets to be chunked."""

    dst_uri: str
    """URI where the chunks should be saved."""

    options: Union[str, ChunkOptions] = ChunkOptions()


class ListChunksInput(PCBaseModel):
    chunkset_uri: str
    """URI to the chunkset."""

    all: bool = False
    """If True, list all chunks. Otherwise only list new or failed chunks."""


class ChunkInfo(PCBaseModel):
    uri: str
    """URI of the chunk."""
    chunk_id: str
    """ID of the chunk."""


class ChunksOutput(PCBaseModel):
    chunks: List[ChunkInfo]
    """List of chunks. Each chunk contain a lists of asset URIs."""


class CreateChunksTaskConfig(TaskDefinition):
    @classmethod
    def create(
        cls,
        image: str,
        args: CreateChunksInput,
        code: Optional[CodeConfig] = None,
        environment: Optional[Dict[str, str]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> "CreateChunksTaskConfig":
        return CreateChunksTaskConfig(
            id=CREATE_CHUNKS_TASK_ID,
            image=image,
            code=code,
            args=args.dict(),
            task=CREATE_CHUNKS_TASK_PATH,
            environment=environment,
            tags=tags,
        )

    @classmethod
    def from_collection(
        cls,
        ds: DatasetDefinition,
        collection: CollectionDefinition,
        chunkset_id: str,
        src_uri: str,
        options: Optional[Union[str, ChunkOptions]] = None,
        environment: Optional[Dict[str, str]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> "CreateChunksTaskConfig":
        chunk_storage_config = collection.chunk_storage
        dst_uri = chunk_storage_config.get_storage().get_uri(
            f"{chunkset_id}/{ASSET_CHUNKS_PREFIX}"
        )

        return cls.create(
            image=ds.image,
            code=ds.code,
            args=CreateChunksInput(
                src_uri=src_uri,
                dst_uri=dst_uri,
                options=options or ChunkOptions(),
            ),
            environment=environment,
            tags=tags,
        )


class ListChunksTaskConfig(TaskDefinition):
    @classmethod
    def create(
        cls,
        image: str,
        args: ListChunksInput,
        task: str = LIST_CHUNKS_TASK_PATH,
        code: Optional[CodeConfig] = None,
        environment: Optional[Dict[str, str]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> "ListChunksTaskConfig":
        return ListChunksTaskConfig(
            id=LIST_CHUNKS_TASK_ID,
            image=image,
            code=code,
            args=args.dict(),
            task=task,
            environment=environment,
            tags=tags,
        )

    @classmethod
    def from_collection(
        cls,
        ds: DatasetDefinition,
        collection: CollectionDefinition,
        chunkset_id: str,
        all: bool = False,
        environment: Optional[Dict[str, str]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> "ListChunksTaskConfig":
        chunk_storage_config = collection.chunk_storage
        chunkset_uri = chunk_storage_config.get_storage().get_uri(
            f"{chunkset_id}/{ASSET_CHUNKS_PREFIX}"
        )

        return cls.create(
            image=ds.image,
            code=ds.code,
            args=ListChunksInput(chunkset_uri=chunkset_uri, all=all),
            task=LIST_CHUNKS_TASK_PATH,
            environment=environment,
            tags=tags,
        )

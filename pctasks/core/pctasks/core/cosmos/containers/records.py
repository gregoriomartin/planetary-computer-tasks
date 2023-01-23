"""A single partition container

This allows for continuation tokens on top-level queries.

PCTasks does not have hierarchical grouping above the "Workflow" level, so to fetch all
all workflows in a paginated way we need a container that has a single partition key.
The Python SDK does not support continuation tokens for cross-partition queries.
"""

from typing import Dict, Optional, Type, TypeVar

from pydantic import BaseModel

from pctasks.core.cosmos.container import (
    AsyncCosmosDBContainer,
    ContainerOperation,
    CosmosDBContainer,
    TriggerType,
)
from pctasks.core.cosmos.database import CosmosDBDatabase
from pctasks.core.cosmos.settings import CosmosDBSettings
from pctasks.core.models.record import TYPE_FIELD_NAME, Record

T = TypeVar("T", bound=Record)

STORED_PROCEDURES: Dict[ContainerOperation, Dict[Type[BaseModel], str]] = {}

TRIGGERS: Dict[ContainerOperation, Dict[TriggerType, str]] = {}


class RecordsContainer(CosmosDBContainer[T]):
    """A container used to store top-level records, partitioned by their type"""

    def __init__(
        self,
        model_type: Type[T],
        db: Optional[CosmosDBDatabase] = None,
        settings: Optional[CosmosDBSettings] = None,
    ) -> None:
        super().__init__(
            lambda settings: settings.get_records_container_name(),
            partition_key=TYPE_FIELD_NAME,
            model_type=model_type,  # type: ignore[arg-type]
            db=db,
            settings=settings,
            stored_procedures=STORED_PROCEDURES,
            triggers=TRIGGERS,
        )

    def get_partition_key(self, model: T) -> str:
        return model.type


class AsyncRecordsContainer(AsyncCosmosDBContainer[T]):
    """A container used to store top-level records, partitioned by their type"""

    def __init__(
        self,
        model_type: Type[T],
        db: Optional[CosmosDBDatabase] = None,
        settings: Optional[CosmosDBSettings] = None,
    ) -> None:
        super().__init__(
            lambda settings: settings.get_records_container_name(),
            partition_key=TYPE_FIELD_NAME,
            model_type=model_type,  # type: ignore[arg-type]
            db=db,
            settings=settings,
            stored_procedures=STORED_PROCEDURES,
            triggers=TRIGGERS,
        )

    def get_partition_key(self, model: T) -> str:
        return model.type

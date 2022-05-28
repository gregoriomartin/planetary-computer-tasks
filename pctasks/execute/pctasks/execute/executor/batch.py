import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple, Union

import azure.batch.models as batchmodels

from pctasks.core.models.record import TaskRunStatus
from pctasks.core.utils import map_opt
from pctasks.execute.batch.client import BatchClient
from pctasks.execute.batch.model import BatchTaskId
from pctasks.execute.batch.task import BatchTask
from pctasks.execute.batch.utils import make_unique_job_id, make_valid_batch_id
from pctasks.execute.constants import MAX_MISSING_POLLS
from pctasks.execute.executor.base import TaskExecutor
from pctasks.execute.models import (
    FailedSubmitResult,
    PreparedTaskSubmitMessage,
    SuccessfulSubmitResult,
    TaskPollResult,
)
from pctasks.execute.settings import BatchSettings

logger = logging.getLogger(__name__)

BATCH_POOL_ID_TAG = "batch_pool_id"


class BatchExecutorError(Exception):
    pass


job_locks: Dict[str, Lock] = defaultdict(Lock)


def get_pool_id(tags: Optional[Dict[str, str]], batch_settings: BatchSettings) -> str:
    return (tags or {}).get(BATCH_POOL_ID_TAG, batch_settings.default_pool_id)


def transfer_index(job_id: str, task_id: str) -> Tuple[str, str]:
    """Transfer an index from a job id to the task id.

    Job IDs can have indexes when created from a
    list through foreach. We want to submit tasks
    for these types of jobs to the same Azure Batch
    job, so remove the index when creating the Azure Batch
    job name, and transfer it to the task id.
    """
    m = re.search(r"\[(\d+)\]", job_id)
    if m:
        result_job_id = re.sub(r"\[\d+\]", "", job_id)
        result_task_id = f"{task_id}_{m.group(1)}"
        return (result_job_id, result_task_id)
    return (job_id, task_id)


@dataclass(frozen=True)
class BatchJobInfo:
    job_prefix: str
    pool_id: str


@dataclass(frozen=True)
class BatchTaskInfo:
    task: BatchTask
    index: int


class BatchTaskExecutor(TaskExecutor):
    def submit(
        self, prepared_tasks: List[PreparedTaskSubmitMessage]
    ) -> List[Union[SuccessfulSubmitResult, FailedSubmitResult]]:

        batch_submits: Dict[BatchJobInfo, List[BatchTaskInfo]] = defaultdict(list)

        with BatchClient(self.settings.batch_settings) as batch_client:

            # Transform the tasks into BatchTasks,
            # grouped by the job the will be submitted to

            for i, prepared_task in enumerate(prepared_tasks):
                submit_msg = prepared_task.task_submit_message
                job_id = submit_msg.job_id
                task_id = submit_msg.config.id
                run_msg = prepared_task.task_run_message
                task_input_blob_config = prepared_task.task_input_blob_config
                task_tags = prepared_task.task_tags

                job_id_for_batch, task_id_for_batch = transfer_index(job_id, task_id)

                pool_id = get_pool_id(task_tags, self.settings.batch_settings)

                command = [
                    "pctasks",
                    "task",
                    "run",
                    task_input_blob_config.uri,
                    "--sas-token",
                    task_input_blob_config.sas_token,
                ]

                if task_input_blob_config.account_url:
                    command.extend(
                        ["--account-url", task_input_blob_config.account_url]
                    )

                batch_job_prefix = make_valid_batch_id(
                    f"{submit_msg.dataset}_{job_id_for_batch}_{pool_id}"
                )
                batch_task_id = make_valid_batch_id(task_id_for_batch)

                batch_task = BatchTask(
                    task_id=batch_task_id,
                    command=command,
                    image=run_msg.config.image,
                )

                batch_submits[BatchJobInfo(batch_job_prefix, pool_id)].append(
                    BatchTaskInfo(batch_task, i)
                )

            # Create any jobs necessary and submit the tasks

            submit_results: Dict[
                int, Union[SuccessfulSubmitResult, FailedSubmitResult]
            ] = {}

            for batch_job_info, batch_task_infos in batch_submits.items():
                job_prefix = batch_job_info.job_prefix
                pool_id = batch_job_info.pool_id

                retry_count = 0
                task_submitted = False
                batch_job_id: Optional[str] = None

                try:
                    with job_locks[job_prefix]:
                        # Try twice in case job completes before we can submit tasks
                        while not task_submitted and retry_count <= 1:
                            try:

                                batch_job_id = batch_client.find_active_job(job_prefix)

                                if not batch_job_id:
                                    # Create the job
                                    if not batch_client.get_pool(pool_id):
                                        raise BatchExecutorError(
                                            f"Batch pool {pool_id} not found."
                                        )

                                    batch_job_id = make_unique_job_id(job_prefix)

                                    batch_job_id = batch_client.add_job(
                                        job_id=batch_job_id,
                                        pool_id=pool_id,
                                        make_unique=False,
                                    )

                                else:
                                    logger.info(
                                        f"Found existing batch job {batch_job_id}."
                                    )

                                if not batch_job_id:
                                    raise BatchExecutorError(
                                        f"Could not create batch job for {job_prefix}."
                                    )

                                # Submit the tasks
                                task_errors = batch_client.add_collection(
                                    batch_job_id,
                                    [i.task for i in batch_task_infos],
                                )

                                task_submitted = True

                                # Process the results from Azure Batch
                                for i, task_error in enumerate(task_errors):
                                    batch_task_info = batch_task_infos[i]
                                    task_id = batch_task_info.task.task_id
                                    if task_error:
                                        err: Any = task_error.message
                                        error_msg = err.value
                                        submit_results[
                                            batch_task_info.index
                                        ] = FailedSubmitResult(errors=[error_msg])
                                    else:
                                        submit_results[
                                            batch_task_info.index
                                        ] = SuccessfulSubmitResult(
                                            executor_id=BatchTaskId(
                                                batch_job_id=batch_job_id,
                                                batch_task_id=task_id,
                                            ).dict(),
                                        )

                            except batchmodels.BatchErrorException as e:
                                logger.exception(e)
                                error: Any = e.error  # Avoid type hinting error
                                if error.code == "JobCompleted":
                                    if retry_count > 1:
                                        raise
                                    retry_count += 1
                                else:
                                    raise

                    if not batch_job_id:
                        raise BatchExecutorError("Failed to create batch job.")

                except Exception as e:
                    logger.exception(e)

                    for batch_task_info in batch_task_infos:
                        submit_results[batch_task_info.index] = FailedSubmitResult(
                            errors=[str(e)]
                        )

        return [submit_results[i] for i in sorted(submit_results)]

    def poll_task(
        self,
        executor_id: Dict[str, Any],
        previous_poll_count: int,
    ) -> TaskPollResult:
        task_id = BatchTaskId.parse_obj(executor_id)
        with BatchClient(self.settings.batch_settings) as batch_client:
            task_status_result = batch_client.get_task_status(
                job_id=task_id.batch_job_id, task_id=task_id.batch_task_id
            )

            if task_status_result is None:
                if previous_poll_count < MAX_MISSING_POLLS:
                    return TaskPollResult(task_status=TaskRunStatus.PENDING)
                else:
                    return TaskPollResult(
                        task_status=TaskRunStatus.FAILED,
                        poll_errors=[
                            f"Batch task not found after {previous_poll_count} polls."
                        ],
                    )
            else:
                task_status, error_message = task_status_result
                return TaskPollResult(
                    task_status=task_status,
                    poll_errors=map_opt(lambda e: [e], error_message),
                )

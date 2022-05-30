import json
import logging
from typing import Any, Dict, List, Union

import requests

from pctasks.core.models.record import TaskRunStatus
from pctasks.execute.executor.base import Executor
from pctasks.execute.models import (
    FailedSubmitResult,
    PreparedTaskSubmitMessage,
    SuccessfulSubmitResult,
    TaskPollResult,
)

logger = logging.getLogger(__name__)


class LocalTaskExecutor(Executor):
    """A local development executor.

    This submits the run arguments to a local executor.
    See the local-executor service in the development environment.
    """

    def __init__(self, local_executor_url: str):
        self.local_executor_url = local_executor_url

    def submit_tasks(
        self, prepared_tasks: List[PreparedTaskSubmitMessage]
    ) -> List[Union[SuccessfulSubmitResult, FailedSubmitResult]]:
        results: List[Union[SuccessfulSubmitResult, FailedSubmitResult]] = []
        for prepared_task in prepared_tasks:
            task_input_blob_config = prepared_task.task_input_blob_config
            task_tags = prepared_task.task_tags
            args = [
                "task",
                "run",
                task_input_blob_config.uri,
                "--sas-token",
                task_input_blob_config.sas_token,
            ]

            if task_input_blob_config.account_url:
                args.extend(["--account-url", task_input_blob_config.account_url])

            data = json.dumps({"args": args, "tags": task_tags or {}}).encode("utf-8")
            resp = requests.post(self.local_executor_url + "/execute", data=data)
            if resp.status_code == 200:
                results.append(SuccessfulSubmitResult(executor_id=resp.json()))
            else:
                results.append(
                    FailedSubmitResult(errors=[f"{resp.status_code}: {resp.text}"])
                )

        return results

    def poll_task(
        self,
        executor_id: Dict[str, Any],
        previous_poll_count: int,
    ) -> TaskPollResult:
        try:
            resp = requests.get(self.local_executor_url + f"/poll/{executor_id['id']}")
            if resp.status_code == 200:
                return TaskPollResult.parse_obj(resp.json())
            elif resp.status_code == 404:
                return TaskPollResult(task_status=TaskRunStatus.PENDING)
            else:
                resp.raise_for_status()
                raise Exception(f"Unexpected status code: {resp.status_code}")
        except Exception as e:
            logger.exception(e)
            return TaskPollResult(task_status=TaskRunStatus.FAILED)

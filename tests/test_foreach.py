"""
Integration tests that tests submitting an Ingest task.
Monitors the task status and ensures the
STAC Collection and Items were successfully created/updated
in the development database.
"""
import textwrap
from pathlib import Path
from pctasks.dev.blob import copy_dir_to_azurite, temp_azurite_blob_storage

from pctasks.dev.test_utils import (
    assert_workflow_is_successful,
    run_workflow,
    run_workflow_from_file,
)

HERE = Path(__file__).parent
WORKFLOWS = HERE / "workflows"
ASSETS_DIR = HERE / "data-files" / "simple-assets"

TIMEOUT_SECONDS = 120


def test_foreach_simple_workflow():
    workflow = textwrap.dedent(
        """\

        name: Test foreach workflow
        dataset: microsoft/test-foreach
        target_environment: staging

        args:
        - task_code_path
        - input_uri
        - output_uri

        jobs:
            list-files:
                name: List Files
                tasks:
                - id: paths
                  image: localhost:5001/pctasks-task-base:latest
                  code: ${{ args.task_code_path }}
                  task: tasks:list_files_task
                  args:
                    uri: ${{ args.input_uri }}

            process:
                name: Read and write file
                needs: list-files
                foreach:
                    items: ${{ jobs.list-files.tasks.paths.output.uris }}
                tasks:
                - id: read-file
                  image: localhost:5001/pctasks-task-base:latest
                  code: ${{ args.task_code_path }}
                  task: tasks:read_file_task
                  args:
                    uri: ${{ item }}
                - id: write-text
                  image: localhost:5001/pctasks-task-base:latest
                  code: ${{ args.task_code_path }}
                  task: tasks:write_file_task
                  args:
                    uri: ${{ args.output_uri}}/${{ tasks.read-file.output.name }}
                    content: ${{ tasks.read-file.output.content }}

        """
    )

    with temp_azurite_blob_storage() as root_storage:
        input_storage = root_storage.get_substorage("input")
        output_storage = root_storage.get_substorage("output")

        copy_dir_to_azurite(input_storage, ASSETS_DIR)

        run_id = run_workflow(
            workflow,
            args={
                "input_uri": input_storage.get_uri(),
                "output_uri": output_storage.get_uri(),
                "task_code_path": str((HERE / "tasks.py").resolve()),
            },
        )

        assert_workflow_is_successful(run_id, timeout_seconds=TIMEOUT_SECONDS)

        expected = {}

        for path in input_storage.list_files():
            name = Path(path).name
            expected[name] = input_storage.read_text(path)

        assert expected

        for path in output_storage.list_files():
            assert path in expected
            assert expected[path] == output_storage.read_text(path)


def test_foreach_full_workflow():

    with temp_azurite_blob_storage() as root_storage:
        input_storage = root_storage.get_substorage("input")
        output_storage = root_storage.get_substorage("output")

        copy_dir_to_azurite(input_storage, ASSETS_DIR)
        run_id = run_workflow_from_file(
            HERE / "workflows" / "test-foreach.yaml",
            args={
                "input_uri": input_storage.get_uri(),
                "output_uri": output_storage.get_uri(),
                "task_code_path": str((HERE / "tasks.py").resolve()),
            },
        )

        for path in input_storage.list_files():
            print(f"{path} = {input_storage.get_uri(path)}")

        assert_workflow_is_successful(run_id, timeout_seconds=TIMEOUT_SECONDS)

        expected = {}

        for path in input_storage.list_files():
            name = Path(path).name
            expected[name] = input_storage.read_text(path)

        assert expected

        for path in output_storage.list_files():
            assert path in expected
            assert expected[path] == output_storage.read_text(path)

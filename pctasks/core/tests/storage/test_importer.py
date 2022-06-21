import importlib.metadata
from pathlib import Path

from pctasks.core.importer import ensure_code
from pctasks.dev.blob import temp_azurite_blob_storage

TESTS = Path(__file__).parent.parent


def test_import_module():
    path = str(TESTS / "data-files/example_module/a.py")
    with temp_azurite_blob_storage() as storage:
        # storage.upload_bytes(src.encode(), "mymodule.py")
        uri = storage.upload_code(path)
        token = "b618be31818766973c94818a9e29a8f6"
        assert uri == f"blob://devstoreaccount1/test-data/{storage.prefix}/{token}/a.py"
        p = ensure_code(f"{token}/a.py", storage)
        assert p.name == "a.py"

        cls = importlib.metadata.EntryPoint("", "a:A", "").load()
        instance = cls()
        result = instance.a()
        assert result == "a"


def test_import_package():
    path = str(TESTS / "data-files/example_module")

    with temp_azurite_blob_storage() as storage:
        uri = storage.upload_code(path)
        token = "7c16da5c8bd566fb687c29ed2a95b900"
        assert uri == (
            f"blob://devstoreaccount1/test-data/{storage.prefix}/"
            f"{token}/example_module.zip"
        )
        result = ensure_code(f"{token}/example_module.zip", storage)
        cls = importlib.metadata.EntryPoint("", "example_module:B", "").load()
        instance = cls()
        assert instance.a() == "a"
        assert instance.b() == "b"
        assert result.name == "example_module.zip"

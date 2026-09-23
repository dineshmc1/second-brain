import os
import shutil
import sys
from pathlib import Path
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("SECOND_BRAIN_DATA_DIR", str(Path(__file__).resolve().parents[1] / ".test-runtime"))

from app.core.database import Database


@pytest.fixture
def tmp_path():
    path = Path(__file__).resolve().parents[1] / ".test-runtime" / str(uuid4())
    path.mkdir(parents=True, exist_ok=False)
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def database(tmp_path):
    instance = Database(tmp_path / "test.sqlite3")
    instance.migrate()
    return instance

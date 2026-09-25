import zipfile
from types import SimpleNamespace

from app.api import data as data_api
from app.repositories.memory_repository import MemoryRepository


def test_export_supports_get_and_post_and_contains_database(database, tmp_path, monkeypatch):
    MemoryRepository(database).create({"title": "Export me", "content": "A fact", "normalized_fact": "A fact"})
    exports = tmp_path / "exports"
    uploads = tmp_path / "uploads"
    exports.mkdir()
    uploads.mkdir()
    monkeypatch.setattr(data_api, "db", database)
    monkeypatch.setattr(data_api, "get_settings", lambda: SimpleNamespace(
        exports_dir=exports,
        uploads_dir=uploads,
        database_path=database.path,
    ))

    route = next(route for route in data_api.router.routes if route.path == "/data/export")
    assert {"GET", "POST"}.issubset(route.methods)
    response = data_api.export_data()
    with zipfile.ZipFile(response.path) as bundle:
        assert {"second_brain.sqlite3", "metadata.json"}.issubset(bundle.namelist())

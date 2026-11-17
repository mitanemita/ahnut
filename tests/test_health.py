import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.models import new_public_id  # noqa: E402

client = TestClient(app)


def test_index_renders():
    r = client.get("/")
    assert r.status_code == 200
    assert "Открытка, от которой ахнут" in r.text


def test_healthz_db_ok():
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json()["db"] == "ok"


def test_public_id_unguessable():
    ids = {new_public_id() for _ in range(1000)}
    assert len(ids) == 1000 and all(len(i) >= 22 for i in ids)

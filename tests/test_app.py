# isort: skip_file
import importlib
import os
import shutil
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def reset_environment():
    for path in ["test_app.db", "storage", "test_storage"]:
        if Path(path).exists():
            if Path(path).is_file():
                Path(path).unlink()
            else:
                shutil.rmtree(path)
    os.environ["DATABASE_URL"] = "sqlite:///./test_app.db"
    os.environ["STORAGE_DIR"] = "test_storage"
    os.environ["SECRET_KEY"] = "test-key"


reset_environment()
sys.path.append(str(Path(__file__).resolve().parents[1]))

import app.config as config  # noqa: E402
import app.database as database  # noqa: E402
import app.models as models  # noqa: E402
import app.security as security  # noqa: E402
import app.storage as storage  # noqa: E402
import app.main as main  # noqa: E402

# Reload modules to ensure they pick up test env values
config = importlib.reload(config)
database = importlib.reload(database)
models = importlib.reload(models)
security = importlib.reload(security)
storage = importlib.reload(storage)
main = importlib.reload(main)

client = TestClient(main.app)


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def login(username: str, password: str) -> str:
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_document_flow():
    # login as bootstrap admin
    admin_token = login("admin", "admin123")

    # create a regular user
    response = client.post(
        "/auth/register",
        json={"username": "alice", "password": "password123", "role": "user"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200, response.text
    user_token = login("alice", "password123")

    # upload a document as admin
    file_content = b"quality-doc-contents"
    response = client.post(
        "/documents",
        headers=auth_headers(admin_token),
        files={"file": ("policy.pdf", file_content, "application/pdf")},
        data={"title": "Quality Policy", "description": "Root policy", "tags": "policy,root"},
    )
    assert response.status_code == 200, response.text
    document_id = response.json()["id"]

    # list documents as user
    response = client.get("/documents", headers=auth_headers(user_token))
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 1
    assert docs[0]["title"] == "Quality Policy"

    # download latest version as user
    response = client.get(f"/documents/{document_id}/download", headers=auth_headers(user_token))
    assert response.status_code == 200
    assert response.content == file_content

    # ensure versions endpoint works
    response = client.get(f"/documents/{document_id}/versions", headers=auth_headers(user_token))
    assert response.status_code == 200
    versions = response.json()
    assert versions[0]["version"] == 1


# Cleanup after tests

def teardown_module(module):
    reset_environment()

import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings


class DocumentStorage:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, upload: UploadFile) -> Path:
        unique_name = f"{uuid.uuid4().hex}_{upload.filename}"
        target = self.base_dir / unique_name
        with target.open("wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)
        return target

    def get_path(self, filename: str) -> Path:
        return self.base_dir / filename


storage = DocumentStorage(settings.storage_dir)

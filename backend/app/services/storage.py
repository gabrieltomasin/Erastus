import os
from pathlib import Path

from app.config import settings


class LocalStorage:
    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.UPLOAD_DIR)

    def get_session_dir(self, session_id: int) -> Path:
        d = self.base_dir / str(session_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(self, session_id: int, filename: str, content: bytes) -> str:
        d = self.get_session_dir(session_id)
        filepath = d / filename
        filepath.write_bytes(content)
        return str(filepath)

    def save_from_file(self, session_id: int, filename: str, source_path: str) -> str:
        d = self.get_session_dir(session_id)
        filepath = d / filename
        Path(source_path).rename(filepath)
        return str(filepath)

    def get_path(self, session_id: int, filename: str) -> str:
        return str(self.get_session_dir(session_id) / filename)

    def delete_session_dir(self, session_id: int) -> None:
        import shutil
        d = self.get_session_dir(session_id)
        if d.exists():
            shutil.rmtree(d)

    def list_files(self, session_id: int) -> list[str]:
        d = self.get_session_dir(session_id)
        if not d.exists():
            return []
        return [str(f) for f in d.iterdir() if f.is_file()]


storage = LocalStorage()

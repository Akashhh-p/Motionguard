import re
from pathlib import Path
from fastapi import HTTPException
from ..config import get_settings


SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(filename: str) -> str:
    cleaned = SAFE_NAME.sub("_", Path(filename).name).strip("._")
    return cleaned or "upload.bin"


def storage_subdir(name: str) -> Path:
    root = get_settings().storage_dir / name
    root.mkdir(parents=True, exist_ok=True)
    return root


def assert_storage_file(path: str | Path) -> Path:
    candidate = Path(path).resolve()
    root = get_settings().storage_dir.resolve()
    if root not in candidate.parents and candidate != root:
        raise HTTPException(status_code=403, detail="File is outside managed storage.")
    if not candidate.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return candidate

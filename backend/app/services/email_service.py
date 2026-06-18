from pathlib import Path
from ..config import get_settings


def write_dev_email(to_email: str, subject: str, body: str) -> Path:
    settings = get_settings()
    outbox = settings.storage_dir / "outbox" / "email_outbox.log"
    outbox.parent.mkdir(parents=True, exist_ok=True)
    with outbox.open("a", encoding="utf-8") as handle:
        handle.write(f"TO: {to_email}\nSUBJECT: {subject}\n{body}\n---\n")
    return outbox


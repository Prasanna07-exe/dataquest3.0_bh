from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.attachment import Attachment


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}

MAX_FILE_SIZE = 10 * 1024 * 1024


def save_attachment(
    db: Session,
    service_request_id: int,
    uploaded_by: int,
    file: UploadFile,
    attachment_type: str = "EVIDENCE",
) -> Attachment:

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError("Unsupported file type.")

    content = file.file.read()

    if len(content) > MAX_FILE_SIZE:
        raise ValueError("File size exceeds 10 MB limit.")

    original_name = file.filename or "attachment"

    stored_name = f"{uuid4().hex}_{original_name}"
    file_path = UPLOAD_DIR / stored_name

    file_path.write_bytes(content)

    attachment = Attachment(
        service_request_id=service_request_id,
        file_name=original_name,
        stored_name=stored_name,
        content_type=file.content_type,
        file_size=len(content),
        file_path=str(file_path),
        attachment_type=attachment_type,
        uploaded_by=uploaded_by,
    )

    db.add(attachment)
    db.flush()

    return attachment
from pathlib import Path
import aiofiles
import uuid

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


async def save_file(file) -> dict:
    if not file.filename:
        raise ValueError("No file provided.")

    name = Path(file.filename).stem
    ext = Path(file.filename).suffix
    unique_filename = f"{name}_{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / unique_filename

    async with aiofiles.open(file_path, "wb") as out_file:
        while chunk := await file.read(1024 * 1024):
            await out_file.write(chunk)

    return {
        "original_filename": file.filename,
        "saved_as": unique_filename,
        "url": f"/uploads/{unique_filename}",
    }

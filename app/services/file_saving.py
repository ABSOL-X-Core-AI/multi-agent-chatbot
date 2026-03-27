import uuid
import logging
import aiofiles
from pathlib import Path
from app.services.file_processor import extract_text, chunk_text, validate_file
from app.services.embeddings import embed_texts
from app.services.db_operations import save_document_chunks

logger = logging.getLogger("uvicorn.error")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


async def save_file(file) -> dict:
    if not file.filename:
        raise ValueError("No file provided.")

    # validate the file type
    validate_file(file.filename)

    # read the content
    content = await file.read()

    # save the file
    name = Path(file.filename).stem
    ext = Path(file.filename).suffix
    unique_filename = f"{name}_{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / unique_filename

    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(content)
    logger.info(f"Saved to disk: {unique_filename}")

    # extract text
    text = extract_text(file.filename, content)
    if not text.strip():
        raise ValueError("No text could be extracted from this file.")

    # chunk
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("File produced no usable text chunks.")
    logger.info(f"Split '{file.filename}' into {len(chunks)} chunks")

    # embed
    embeddings = embed_texts(chunks)

    # save to pgvector using original filename as key
    saved = await save_document_chunks(file.filename, chunks, embeddings)
    logger.info(f"Saved {saved} embeddings for '{file.filename}'")

    return {
        "original_filename": file.filename,
        "saved_as": unique_filename,
        "url": f"/uploads/{unique_filename}",
        "chunks_saved": saved,
    }

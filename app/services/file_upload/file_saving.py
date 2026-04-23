import uuid
import logging
import aiofiles
from pathlib import Path
from langfuse import get_client
from app.services.embeddings import embed_texts
from app.services.file_upload.file_processor import (
    extract_text,
    chunk_text,
    validate_file,
)
from app.services.db_services.db_operations import save_document_chunks

logger = logging.getLogger("uvicorn.error")
langfuse = get_client()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


async def save_file(file) -> dict:
    if not file.filename:
        raise ValueError("No file provided.")

    with langfuse.start_as_current_observation(
        as_type="span",
        name="file-upload",
        input={"filename": file.filename},
    ) as trace:

        # validate
        validate_file(file.filename)
        content = await file.read()

        # save to disk
        name = Path(file.filename).stem
        ext = Path(file.filename).suffix
        unique_filename = f"{name}_{uuid.uuid4().hex}{ext}"
        file_path = UPLOAD_DIR / unique_filename
        async with aiofiles.open(file_path, "wb") as out_file:
            await out_file.write(content)
        logger.info(f"Saved to disk: {unique_filename}")

        # extract text
        with langfuse.start_as_current_observation(
            as_type="span",
            name="extract-text",
            input={"filename": file.filename},
        ) as extract_span:
            try:
                text = extract_text(file.filename, content)
                if not text.strip():
                    raise ValueError("No text could be extracted from this file.")
                extract_span.update(output={"char_count": len(text)})

            except Exception as e:
                extract_span.update(level="ERROR", status_message=str(e))
                raise

        # chunk
        with langfuse.start_as_current_observation(
            as_type="span",
            name="chunk-text",
            input={"char_count": len(text)},
        ) as chunk_span:
            try:
                chunks = chunk_text(text)
                if not chunks:
                    raise ValueError("File produced no usable text chunks.")
                logger.info(f"Split '{file.filename}' into {len(chunks)} chunks")
                chunk_span.update(output={"chunk_count": len(chunks)})
            except Exception as e:
                chunk_span.update(level="ERROR", status_message=str(e))
                raise

        # embed
        with langfuse.start_as_current_observation(
            as_type="span",
            name="embed-chunks",
            input={"chunk_count": len(chunks)},
        ) as embed_span:
            try:
                embeddings = embed_texts(chunks)
                embed_span.update(
                    output={"embedding_dim": len(embeddings[0]) if embeddings else 0}
                )
            except Exception as e:
                embed_span.update(level="ERROR", status_message=str(e))
                raise

        # save to DB
        with langfuse.start_as_current_observation(
            as_type="span",
            name="save-to-db",
            input={"filename": file.filename, "chunk_count": len(chunks)},
        ) as db_span:
            try:
                saved = await save_document_chunks(file.filename, chunks, embeddings)
                logger.info(f"Saved {saved} embeddings for '{file.filename}'")
                db_span.update(output={"saved": saved})
            except Exception as e:
                db_span.update(level="ERROR", status_message=str(e))
                raise

        trace.update(
            output={
                "original_filename": file.filename,
                "saved_as": unique_filename,
                "chunks_saved": saved,
            }
        )

    return {
        "original_filename": file.filename,
        "saved_as": unique_filename,
        "url": f"/uploads/{unique_filename}",
        "chunks_saved": saved,
    }

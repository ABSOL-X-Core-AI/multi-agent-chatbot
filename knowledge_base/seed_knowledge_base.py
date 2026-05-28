import logging
from pathlib import Path
from app.services.embeddings import embed_texts
from app.services.file_upload.file_processor import (
    extract_text,
    chunk_text,
    validate_file,
)
from app.services.db_services.db_operations import save_document_chunks
from app.services.db_services.database import create_tables

logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(message)s")
logger = logging.getLogger(__name__)

KNOWLEDGE_BASE_DIR = Path("Gro4ce_AI_Agent_Knowledge_Base_v1")


async def seed_file(file_path: Path):
    """Process and seed a single file into pgvector."""

    logger.info(f"Processing '{file_path.name}'...")

    # 1. Validate the file type (.txt, .pdf, .docx)
    try:
        validate_file(file_path.name)
    except ValueError as e:
        logger.warning(f"Skipping '{file_path.name}': {e}")
        return

    # 2. Read the raw bytes from disk
    content = file_path.read_bytes()

    # 3. Extract plain text — handles .txt, .pdf, .docx automatically
    text = extract_text(file_path.name, content)
    if not text.strip():
        logger.warning(f"Skipping '{file_path.name}': no text could be extracted")
        return

    # 4. Split into chunks
    chunks = chunk_text(text)
    if not chunks:
        logger.warning(f"Skipping '{file_path.name}': produced no chunks")
        return
    logger.info(f"Split into {len(chunks)} chunks")

    # 5. Generate embeddings for all chunks
    embeddings = embed_texts(chunks)
    logger.info(f"Generated {len(embeddings)} embeddings")

    # 6. Save to pgvector
    saved = await save_document_chunks(file_path.name, chunks, embeddings)
    logger.info(f"Saved {saved} chunks for '{file_path.name}'")


async def seed_all():
    """Seed every file in the knowledge_base/ folder."""

    await create_tables()

    if not KNOWLEDGE_BASE_DIR.exists():
        logger.error(
            f"Folder '{KNOWLEDGE_BASE_DIR}' does not exist. Create it and add your files."
        )
        return

    files = list(KNOWLEDGE_BASE_DIR.iterdir())
    if not files:
        logger.warning(f"No files found in '{KNOWLEDGE_BASE_DIR}'. Nothing to seed.")
        return

    logger.info(f"Found {len(files)} file(s) in '{KNOWLEDGE_BASE_DIR}'")

    for file_path in files:
        if file_path.is_file():
            await seed_file(file_path)

    logger.info("Seeding complete.")

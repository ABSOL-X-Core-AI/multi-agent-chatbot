import io
import logging
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger("uvicorn.error")

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx"}


splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=64,
    separators=["\n\n", "\n", ".", " ", ""],
)


def validate_file(filename: str):
    # Raise ValueError if file type or size is invalid.
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Invalid file type: '{ext}'. "
            f"Please upload one of the supported formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )


def extract_text(filename: str, content: bytes) -> str:
    # Extract plain text from file bytes based on file extension.
    ext = Path(filename).suffix.lower()

    try:
        if ext == ".txt":
            return content.decode("utf-8", errors="ignore")

        elif ext == ".pdf":
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)

        elif ext == ".docx":
            import docx

            doc = docx.Document(io.BytesIO(content))
            return "\n".join(para.text for para in doc.paragraphs)

        else:
            # fallback for unknown types
            return content.decode("utf-8", errors="ignore")

    except Exception as e:
        logger.error(f"Text extraction failed for '{filename}': {e}")
        raise ValueError(f"Could not extract text from file: {e}")


def chunk_text(text: str) -> list[str]:
    # Split text into overlapping chunks.
    chunks = splitter.split_text(text)
    return [c.strip() for c in chunks if len(c.strip()) > 0]

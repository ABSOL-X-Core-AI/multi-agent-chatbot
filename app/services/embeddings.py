import os
import torch
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")

model = SentenceTransformer(
    MODEL_NAME,
    cache_folder=MODEL_DIR,
    model_kwargs={"torch_dtype": torch.float16},
    tokenizer_kwargs={"padding_side": "left"},
    device=DEVICE,
)

model.eval()


def embed_texts(texts: list[str]) -> list[list[float]]:
    with torch.no_grad():
        return model.encode(texts, normalize_embeddings=True).tolist()


def embed_query(query: str) -> list[float]:
    task = "Given a user query, retrieve relevant document passages"
    with torch.no_grad():
        return model.encode(
            query, prompt=f"Instruct: {task}\nQuery:", normalize_embeddings=True
        ).tolist()

from fastapi import FastAPI
from .routes import upload

app = FastAPI(
    title="File Upload API",
)

app.include_router(upload.router)


@app.get("/health")
async def health_check():
    """Simple liveness probe."""
    return {"status": "ok"}

from fastapi import APIRouter, UploadFile, File, HTTPException
from ..services.file_saving import save_file

router = APIRouter()


# Uploads a single file and saves it to the uploads directory
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        result = await save_file(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
    finally:
        await file.close()
    return {"message": "File uploaded successfully", **result}

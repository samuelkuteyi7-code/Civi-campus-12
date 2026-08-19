import os
import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request

from App.routes.auth import get_current_user
from App.models.user import User
from App.core.limiter import limiter

router = APIRouter(prefix="/media", tags=["Media"])

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


# 10/minute/IP — uploads hit Cloudinary (real cost) so this is tighter than
# the global default. Real users uploading one photo at a time won't notice.
@router.post("/upload")
@limiter.limit("10/minute")
async def upload_media(request: Request, file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large. Max size is 5MB.")

    try:
        result = cloudinary.uploader.upload(
            contents,
            folder="civiai_campus_reports",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    return {"url": result.get("secure_url")}

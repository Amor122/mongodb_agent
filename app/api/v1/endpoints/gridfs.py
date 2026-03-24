from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, Response, Path, Body, UploadFile, File
from motor.motor_asyncio import AsyncIOMotorDatabase
import urllib.parse

from app.services.gridfs_service import GridFSService
from app.api.dependencies import get_db
from app.models.gridfs import FileInfo

router = APIRouter()


@router.post("/bucket/{bucket_name}/upload")
async def upload_file(
        bucket_name: str = Path(...),
        file: UploadFile = File(...),
        db: AsyncIOMotorDatabase = Depends(get_db)
):
    service = GridFSService(db)
    file_id = await service.upload_file(bucket_name, file)
    return {
        "status": "success",
        "file_id": str(file_id),
        "filename": file.filename
    }


@router.post("/bucket/{bucket_name}/search", response_model=List[FileInfo])
async def search_files(
        bucket_name: str = Path(...),
        query: Dict = Body(...),
        db: AsyncIOMotorDatabase = Depends(get_db)
):
    service = GridFSService(db)
    return await service.search_files(bucket_name, query)


@router.get("/bucket/{bucket_name}/download/{file_id}")
async def download_file(
        bucket_name: str = Path(...),
        file_id: str = Path(...),
        db: AsyncIOMotorDatabase = Depends(get_db)
):
    service = GridFSService(db)
    stream, info = await service.download_file(bucket_name, file_id)
    if not stream or not info:
        raise HTTPException(status_code=404, detail="File not found")

    fname = info["filename"]
    enc = urllib.parse.quote(fname)
    headers = {
        "Content-Disposition": f'attachment; filename="{fname}"; filename*=UTF-8\'\'{enc}',
        "Content-Type": info.get("contentType", "application/octet-stream"),
        "Content-Length": str(info["length"])
    }
    return Response(content=stream, headers=headers)


@router.delete("/bucket/{bucket_name}/delete/{file_id}")
async def delete_file(
        bucket_name: str = Path(...),
        file_id: str = Path(...),
        db: AsyncIOMotorDatabase = Depends(get_db)
):
    service = GridFSService(db)
    try:
        await service.delete_file(bucket_name, file_id)
        return {"status": "success", "message": "File deleted"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Delete failed: {str(e)}")

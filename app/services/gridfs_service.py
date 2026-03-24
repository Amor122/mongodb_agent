from typing import Optional, Tuple, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorGridFSBucket
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import UploadFile, HTTPException


class GridFSService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def upload_file(self, bucket_name: str, file: UploadFile) -> ObjectId:
        bucket = AsyncIOMotorGridFSBucket(self.db, bucket_name=bucket_name)
        file_id = await bucket.upload_from_stream(
            filename=file.filename,
            source=file.file,
            metadata={"content_type": file.content_type}
        )
        return file_id

    async def search_files(self, bucket: str, query: Dict) -> List[Dict[str, Any]]:
        coll = self.db[f"{bucket}.files"]
        cur = coll.find(query)
        out = []
        async for f in cur:
            f["_id"] = str(f["_id"])
            if "uploadDate" in f:
                f["uploadDate"] = f["uploadDate"].isoformat()
            out.append(f)
        return out

    async def download_file(self, bucket: str, file_id: str) -> Tuple[Optional[bytes], Optional[Dict]]:
        try:
            oid = ObjectId(file_id)
        except InvalidId:
            return None, None

        coll = self.db[f"{bucket}.files"]
        info = await coll.find_one({"_id": oid})
        if not info:
            return None, None

        bkt = AsyncIOMotorGridFSBucket(self.db, bucket_name=bucket)
        grid_out = await bkt.open_download_stream(oid)
        content = await grid_out.read()
        return content, info

    async def delete_file(self, bucket_name: str, file_id: str):
        try:
            oid = ObjectId(file_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid file ID format")

        bucket = AsyncIOMotorGridFSBucket(self.db, bucket_name=bucket_name)
        await bucket.delete(oid)

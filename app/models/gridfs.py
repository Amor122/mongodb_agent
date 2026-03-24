from pydantic import BaseModel
from typing import Optional, Dict, Any


class FileInfo(BaseModel):
    _id: str
    filename: str
    length: int
    uploadDate: Optional[str] = None
    contentType: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "_id": "60d21b4667d0d8992e610c87",
                "filename": "test.pdf",
                "length": 102400,
                "uploadDate": "2025-01-01T12:00:00",
                "contentType": "application/pdf",
                "metadata": {"type": "report"}
            }
        }

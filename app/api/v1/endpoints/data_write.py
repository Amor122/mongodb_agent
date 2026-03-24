from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.data_write import WriteRequest
from app.services.data_write_service import DataWriteService
from app.api.dependencies import get_db

router = APIRouter()


@router.post(
    "/write",
    summary="Perform the data write operation. (INSERT, UPDATE, DELETE)"
)
async def write_data(
        request: WriteRequest,
        db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    A universal endpoint for performing insert, update, or delete operations on a specified collection.
    **Please use this endpoint with caution and add strict permission controls in the production environment. **
    """
    try:
        service = DataWriteService(db)
        # Convert Pydantic models to dictionaries for more flexible processing.
        result = await service.write(request.dict(exclude_none=True))
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # In the production environment, more detailed error logs should be recorded.
        raise HTTPException(status_code=500, detail=f"Write operation failed: {str(e)}")

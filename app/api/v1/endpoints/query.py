from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.query import QueryRequest, QueryResponse
from app.services.query_service import QueryService
from app.api.dependencies import get_db

router = APIRouter()


@router.post("/", response_model=QueryResponse, summary="MongoDB query agent")
async def query_mongodb(
    request: QueryRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    try:
        service = QueryService(db)
        result = await service.query(
            collection=request.collection,
            filter=request.filter,
            projection=request.projection,
            sort=request.sort,
            limit=request.limit,
            skip=request.skip
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
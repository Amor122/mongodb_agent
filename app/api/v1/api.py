from fastapi import APIRouter
from app.api.v1.endpoints import gridfs, query, data_write

api_router = APIRouter()
api_router.include_router(query.router, prefix="/query", tags=["query"])
api_router.include_router(gridfs.router, prefix="/gridfs", tags=["gridfs"])
api_router.include_router(data_write.router, prefix="/data", tags=["data-write"])

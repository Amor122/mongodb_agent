from fastapi import Request, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase


async def get_db(request: Request) -> AsyncIOMotorDatabase:
    if not hasattr(request.app.state, "db"):
        raise HTTPException(status_code=503, detail="The database has not been initialized.")
    return request.app.state.db

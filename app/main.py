from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import logging

from app.config import settings
from app.api.v1.api import api_router

# Log configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Resource management during application startup and shutdown"""
    # At startup: Initialize MongoDB connection
    logger.info("Application is starting up, connecting to MongoDB...")
    try:
        # Create MongoDB client (singleton)
        mongo_client = AsyncIOMotorClient(settings.MONGODB_URI)
        # Obtain the database instance
        db = mongo_client[settings.MONGODB_DB_NAME]
        # Verify connection
        await mongo_client.admin.command("ping")
        logger.info("MongoDB Connection successful")

        # Mount the client and database instances to app.state for dependency injection purposes.
        app.state.mongo_client = mongo_client
        app.state.db = db
    except Exception as e:
        logger.error(f"MongoDB connection fail：{str(e)}", exc_info=True)
        # If the connection fails, the application startup will be terminated.
        raise
    # During the application's operation (with the yield serving as the dividing point)
    yield

    # When closing: Release resources
    logger.info("Application is being closed. Disconnecting MongoDB connection...")
    if hasattr(app.state, "mongo_client"):
        app.state.mongo_client.close()
        logger.info("MongoDB disconnected")


app = FastAPI(
    title="simple mongo agent",
    description="Support traditional dataset operations and file search and streaming download for multiple datasets (Buckets)",
    version="1.0.0",
    lifespan=lifespan
)

# Cross-domain configuration (For production environment, please limit the "allow_origins" to specific domains only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", summary="health check")
async def health_check():
    return {
        "status": "ok",
        "version": "3.0.0",
        "async_mode": True
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

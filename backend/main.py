"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from config import settings
from api.routes import router
from api.routes_ingest import router as ingest_router

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    f"{settings.log_dir}/app.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG"
)

# Create FastAPI app
app = FastAPI(
    title="Fashion AI System",
    description="AI-powered fashion visual search, similarity matching, and outfit recommendation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1", tags=["fashion-ai"])
app.include_router(ingest_router, prefix="/api/v1", tags=["ingestion"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Fashion AI System...")
    logger.info(f"API running on http://{settings.api_host}:{settings.api_port}")
    
    # Initialize services (lazy loading will happen on first request)
    try:
        from services import get_embedding_service, get_detection_service
        
        # Pre-load models (optional - can be lazy loaded)
        logger.info("Pre-loading AI models...")
        # get_embedding_service()
        # get_detection_service()
        logger.info("Startup complete!")
    except Exception as e:
        logger.warning(f"Service initialization warning: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Fashion AI System...")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Fashion AI System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug
    )

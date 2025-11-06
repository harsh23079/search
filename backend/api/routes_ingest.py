"""API routes for data ingestion."""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import Optional
from loguru import logger
import os
import tempfile
import time

from services.data_ingestion import DataIngestionService

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/csv")
async def ingest_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    image_url_column: str = "image_url",
    product_name_column: str = "product_name",
    category_column: str = "category",
    validate_categories: bool = True,
    batch_size: int = 10,
    skip_existing: bool = True
):
    """
    Upload CSV file to ingest products into the vector database.
    
    CSV should contain:
    - Image URLs
    - Product names
    - Categories (optional, will be validated/corrected)
    - Any other metadata (price, brand, etc.)
    """
    try:
        # Save uploaded file temporarily
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Run ingestion in background
        ingestion_id = f"ingest_{int(time.time())}"
        
        background_tasks.add_task(
            _run_ingestion,
            tmp_path,
            image_url_column,
            product_name_column,
            category_column,
            validate_categories,
            batch_size,
            skip_existing,
            ingestion_id
        )
        
        return {
            "status": "started",
            "ingestion_id": ingestion_id,
            "message": "Ingestion started in background. Check status endpoint for progress."
        }
    
    except Exception as e:
        logger.error(f"Error starting ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{ingestion_id}")
async def get_ingestion_status(ingestion_id: str):
    """Get status of a running ingestion."""
    # TODO: Implement status tracking
    return {
        "ingestion_id": ingestion_id,
        "status": "running",
        "message": "Status tracking not yet implemented"
    }


def _run_ingestion(
    csv_path: str,
    image_url_column: str,
    product_name_column: str,
    category_column: str,
    validate_categories: bool,
    batch_size: int,
    skip_existing: bool,
    ingestion_id: str
):
    """Run ingestion in background."""
    try:
        service = DataIngestionService()
        stats = service.ingest_from_csv(
            csv_path=csv_path,
            image_url_column=image_url_column,
            product_name_column=product_name_column,
            category_column=category_column,
            validate_categories=validate_categories,
            batch_size=batch_size,
            skip_existing=skip_existing
        )
        logger.info(f"Ingestion {ingestion_id} completed: {stats}")
    except Exception as e:
        logger.error(f"Ingestion {ingestion_id} failed: {e}")
    finally:
        # Clean up temp file
        if os.path.exists(csv_path):
            os.unlink(csv_path)


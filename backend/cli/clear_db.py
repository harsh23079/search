"""CLI command to clear all products from Qdrant database."""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click
from loguru import logger
from config import settings
from qdrant_client import QdrantClient

@click.command()
@click.option("--confirm", is_flag=True, help="Confirm deletion (required)")
def clear_db(confirm: bool):
    """
    Clear all products from the Qdrant database.
    
    WARNING: This will delete all products! Use with caution.
    """
    if not confirm:
        click.echo("ERROR: This will delete all products from the database!")
        click.echo("Use --confirm flag to proceed.")
        sys.exit(1)
    
    try:
        client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )
        
        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if settings.qdrant_collection_name not in collection_names:
            click.echo(f"Collection '{settings.qdrant_collection_name}' does not exist. Nothing to clear.")
            return
        
        # Get current count
        collection_info = client.get_collection(settings.qdrant_collection_name)
        current_count = collection_info.points_count
        
        click.echo(f"Collection '{settings.qdrant_collection_name}' has {current_count} products.")
        click.echo("Deleting all products...")
        
        # Delete collection and recreate it
        client.delete_collection(settings.qdrant_collection_name)
        
        # Recreate empty collection
        from qdrant_client.models import Distance, VectorParams
        client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config=VectorParams(
                size=settings.qdrant_embedding_dim,
                distance=Distance.COSINE
            )
        )
        
        click.echo(f"Successfully cleared {current_count} products from database.")
        click.echo("Collection has been recreated and is ready for new data.")
        
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        click.echo(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    clear_db()


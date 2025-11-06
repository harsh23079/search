"""CLI command for data ingestion."""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click
from typing import Optional
from loguru import logger

from services.data_ingestion import DataIngestionService


@click.command()
@click.argument("csv_path", type=click.Path(exists=True))
@click.option("--image-url-column", default="image_url", help="Column name for image URLs")
@click.option("--product-name-column", default="product_name", help="Column name for product names")
@click.option("--category-column", default="category", help="Column name for categories")
@click.option("--validate-categories/--no-validate-categories", default=True, 
              help="Validate/correct categories using detection model")
@click.option("--batch-size", default=10, help="Number of products to process in each batch")
@click.option("--skip-existing/--no-skip-existing", default=True,
              help="Skip products that already exist in database")
@click.option("--output", type=click.Path(), help="Save ingestion statistics to JSON file")
def ingest(
    csv_path: str,
    image_url_column: str,
    product_name_column: str,
    category_column: str,
    validate_categories: bool,
    batch_size: int,
    skip_existing: bool,
    output: Optional[str]
):
    """
    Ingest products from CSV file into the vector database.
    
    CSV file should contain at minimum:
    - Image URLs (column specified by --image-url-column)
    - Product names (column specified by --product-name-column)
    - Categories (column specified by --category-column, optional)
    
    Example CSV format:
    image_url,product_name,category,price,brand
    https://example.com/image1.jpg,Nike Sneakers,shoes,99.99,Nike
    https://example.com/image2.jpg,Blue Jeans,apparel,49.99,Levi's
    """
    logger.info(f"Starting data ingestion from {csv_path}")
    
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
        
        # Print statistics
        click.echo("\n" + "="*60)
        click.echo("INGESTION STATISTICS")
        click.echo("="*60)
        click.echo(f"Total products:        {stats['total']}")
        click.echo(f"Processed:             {stats['processed']}")
        click.echo(f"Successful:            {stats['successful']}")
        click.echo(f"Failed:                {stats['failed']}")
        click.echo(f"Category corrected:    {stats['category_corrected']}")
        click.echo(f"Skipped:               {stats['skipped']}")
        click.echo("="*60)
        
        if stats['errors']:
            click.echo(f"\nErrors ({len(stats['errors'])}):")
            for error in stats['errors'][:10]:  # Show first 10 errors
                click.echo(f"  - {error}")
            if len(stats['errors']) > 10:
                click.echo(f"  ... and {len(stats['errors']) - 10} more errors")
        
        # Save to file if requested
        if output:
            import json
            with open(output, 'w') as f:
                json.dump(stats, f, indent=2)
            click.echo(f"\nStatistics saved to {output}")
        
        # Exit with error code if failures
        if stats['failed'] > 0:
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    ingest()


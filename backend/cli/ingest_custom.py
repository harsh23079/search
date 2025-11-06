"""CLI command for data ingestion with custom CSV format mapping."""
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
@click.option("--image-column", default="featured_image", 
              help="Column name for image URLs (default: featured_image)")
@click.option("--name-column", default="title",
              help="Column name for product names (default: title)")
@click.option("--category-column", default="category",
              help="Column name for categories (default: category)")
@click.option("--price-column", default="lowest_price",
              help="Column name for prices (default: lowest_price)")
@click.option("--brand-column", default="brand_name",
              help="Column name for brand (default: brand_name)")
@click.option("--validate-categories/--no-validate-categories", default=True,
              help="Validate/correct categories using detection model")
@click.option("--batch-size", default=10, help="Number of products per batch")
@click.option("--skip-existing/--no-skip-existing", default=True,
              help="Skip products already in database")
@click.option("--output", type=click.Path(), help="Save statistics to JSON file")
@click.option("--limit", type=int, help="Limit number of products to process (for testing)")
def ingest_custom(
    csv_path: str,
    image_column: str,
    name_column: str,
    category_column: str,
    price_column: str,
    brand_column: str,
    validate_categories: bool,
    batch_size: int,
    skip_existing: bool,
    output: Optional[str],
    limit: Optional[int]
):
    """
    Ingest products from CSV file with custom column mapping.
    
    Designed for CSV format with:
    - featured_image: Image URLs
    - title: Product names
    - category: Categories (will be auto-corrected if wrong)
    - lowest_price: Prices
    - brand_name: Brand names
    - Many other metadata columns
    
    Example:
        uv run python cli/ingest_custom.py examples/sample_data.csv
    """
    logger.info(f"Starting data ingestion from {csv_path}")
    
    try:
        service = DataIngestionService()
        
        # Use the custom column names
        stats = service.ingest_from_csv(
            csv_path=csv_path,
            image_url_column=image_column,
            product_name_column=name_column,
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
    ingest_custom()


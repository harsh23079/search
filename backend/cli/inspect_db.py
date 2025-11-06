"""CLI tool to inspect ingested data in Qdrant."""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click
from qdrant_client import QdrantClient
from config import settings
import json
from typing import Optional


@click.command()
@click.option("--count", is_flag=True, help="Show total count of products")
@click.option("--list", is_flag=True, help="List all products")
@click.option("--limit", default=10, help="Limit number of products to show (default: 10)")
@click.option("--product-id", help="Show details for specific product ID")
@click.option("--category", help="Filter by category (clothing, shoes, bags, accessories)")
@click.option("--search", help="Search products by name")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--stats", is_flag=True, help="Show statistics about ingested data")
def inspect(
    count: bool,
    list: bool,
    limit: int,
    product_id: Optional[str],
    category: Optional[str],
    search: Optional[str],
    json_output: bool,
    stats: bool
):
    """
    Inspect ingested products in Qdrant vector database.
    
    Examples:
        # Show total count
        uv run python cli/inspect_db.py --count
        
        # List first 10 products
        uv run python cli/inspect_db.py --list
        
        # Show statistics
        uv run python cli/inspect_db.py --stats
        
        # Search by name
        uv run python cli/inspect_db.py --search "Nike"
        
        # Filter by category
        uv run python cli/inspect_db.py --category shoes
    """
    try:
        client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )
        
        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if settings.qdrant_collection_name not in collection_names:
            click.echo(f"❌ Collection '{settings.qdrant_collection_name}' does not exist.")
            click.echo("   No data has been ingested yet.")
            return
        
        collection_info = client.get_collection(settings.qdrant_collection_name)
        total_points = collection_info.points_count
        
        # Show count
        if count:
            click.echo(f"Total products in database: {total_points}")
            return
        
        if total_points == 0:
            click.echo("❌ No products found in database.")
            return
        
        # Show statistics
        if stats:
            show_stats(client, total_points, json_output)
            return
        
        # Show specific product
        if product_id:
            show_product(client, product_id, json_output)
            return
        
        # Search products
        if search:
            search_products(client, search, limit, json_output)
            return
        
        # List products
        if list or (not any([count, product_id, search, stats])):
            list_products(client, limit, category, json_output)
            return
            
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        import traceback
        if json_output:
            click.echo(json.dumps({"error": str(e)}))
        else:
            click.echo(traceback.format_exc())
        sys.exit(1)


def show_stats(client: QdrantClient, total_points: int, json_output: bool):
    """Show statistics about ingested data."""
    # Get sample of points to analyze
    sample_size = min(100, total_points)
    points = client.scroll(
        collection_name=settings.qdrant_collection_name,
        limit=sample_size
    )[0]
    
    categories = {}
    brands = {}
    category_corrected = 0
    
    for point in points:
        payload = point.payload
        category = payload.get("category", "unknown")
        categories[category] = categories.get(category, 0) + 1
        
        brand = payload.get("brand")
        if brand:
            brands[brand] = brands.get(brand, 0) + 1
        
        if payload.get("category_corrected", False):
            category_corrected += 1
    
    stats = {
        "total_products": total_points,
        "categories": categories,
        "top_brands": dict(sorted(brands.items(), key=lambda x: x[1], reverse=True)[:10]),
        "category_corrected": category_corrected,
        "correction_rate": f"{(category_corrected / sample_size * 100):.1f}%" if sample_size > 0 else "0%"
    }
    
    if json_output:
        click.echo(json.dumps(stats, indent=2))
    else:
        click.echo("=" * 60)
        click.echo("DATABASE STATISTICS")
        click.echo("=" * 60)
        click.echo(f"Total products:        {stats['total_products']}")
        click.echo(f"Category corrections:  {stats['category_corrected']} ({stats['correction_rate']})")
        click.echo("")
        click.echo("Products by category:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            click.echo(f"  {cat:20} {count}")
        click.echo("")
        click.echo("Top brands:")
        for brand, count in list(stats['top_brands'].items())[:10]:
            click.echo(f"  {brand:20} {count}")
        click.echo("=" * 60)


def show_product(client: QdrantClient, product_id: str, json_output: bool):
    """Show details for a specific product."""
    try:
        points = client.retrieve(
            collection_name=settings.qdrant_collection_name,
            ids=[product_id]
        )
        
        if not points:
            click.echo(f"❌ Product '{product_id}' not found.")
            return
        
        payload = points[0].payload
        
        if json_output:
            click.echo(json.dumps(payload, indent=2, default=str))
        else:
            click.echo("=" * 60)
            click.echo(f"PRODUCT: {product_id}")
            click.echo("=" * 60)
            click.echo(f"Name:        {payload.get('name', 'N/A')}")
            click.echo(f"Brand:       {payload.get('brand', 'N/A')}")
            click.echo(f"Category:    {payload.get('category', 'N/A')}")
            click.echo(f"Subcategory: {payload.get('subcategory', 'N/A')}")
            click.echo(f"Price:       {payload.get('price', 0):.2f} {payload.get('currency', 'INR')}")
            click.echo(f"Image URL:   {payload.get('image_url', 'N/A')}")
            if payload.get('category_corrected'):
                click.echo(f"CSV Category: {payload.get('csv_category', 'N/A')} (was corrected)")
            click.echo("=" * 60)
            
    except Exception as e:
        click.echo(f"❌ Error retrieving product: {e}", err=True)


def search_products(client: QdrantClient, search_term: str, limit: int, json_output: bool):
    """Search products by name."""
    # Scroll through all points and filter
    points = client.scroll(
        collection_name=settings.qdrant_collection_name,
        limit=1000  # Search in first 1000
    )[0]
    
    matches = []
    search_lower = search_term.lower()
    
    for point in points:
        payload = point.payload
        name = payload.get("name", "").lower()
        if search_lower in name:
            matches.append({
                "product_id": point.id,
                "name": payload.get("name"),
                "category": payload.get("category"),
                "brand": payload.get("brand"),
                "price": payload.get("price")
            })
        if len(matches) >= limit:
            break
    
    if json_output:
        click.echo(json.dumps(matches, indent=2))
    else:
        click.echo(f"Found {len(matches)} products matching '{search_term}':")
        click.echo("")
        for match in matches[:limit]:
            click.echo(f"  {match['product_id']}: {match['name']} ({match['category']}) - {match['brand']}")


def list_products(client: QdrantClient, limit: int, category: Optional[str], json_output: bool):
    """List products."""
    # Scroll all points (or large batch if category filter needed)
    scroll_limit = limit * 10 if category else limit  # Get more if filtering
    points = client.scroll(
        collection_name=settings.qdrant_collection_name,
        limit=scroll_limit
    )[0]
    
    # Filter by category in Python if needed
    if category:
        points = [p for p in points if p.payload.get("category") == category]
        points = points[:limit]  # Limit after filtering
    
    if json_output:
        products = []
        for point in points:
            products.append({
                "product_id": point.id,
                **point.payload
            })
        click.echo(json.dumps(products, indent=2, default=str))
    else:
        click.echo(f"{'=' * 60}")
        if category:
            click.echo(f"PRODUCTS (Category: {category})")
        else:
            click.echo(f"PRODUCTS (showing {len(points)} of {client.get_collection(settings.qdrant_collection_name).points_count})")
        click.echo(f"{'=' * 60}")
        click.echo("")
        
        for point in points:
            payload = point.payload
            click.echo(f"ID:      {point.id}")
            click.echo(f"Name:    {payload.get('name', 'N/A')}")
            click.echo(f"Brand:   {payload.get('brand', 'N/A')}")
            click.echo(f"Category:{payload.get('category', 'N/A')}")
            click.echo(f"Price:   {payload.get('price', 0):.2f} {payload.get('currency', 'INR')}")
            if payload.get('category_corrected'):
                click.echo(f"         (Category corrected from: {payload.get('csv_category', 'N/A')})")
            click.echo("-" * 60)


if __name__ == "__main__":
    inspect()


"""Database configuration and session management."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from loguru import logger
from config import settings
import os

# Determine database URL
if settings.database_url:
    DATABASE_URL = settings.database_url
else:
    # Fallback to SQLite (for development)
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "instagram_posts.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"

# Import aiosqlite for SQLite support if needed
if "sqlite" in DATABASE_URL:
    try:
        import aiosqlite
    except ImportError:
        logger.warning("aiosqlite not installed. SQLite support may not work.")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    try:
        # Import all models to ensure they're registered with Base
        from models.instagram_post import InstagramPost
        from models.extracted_fashion_item import ExtractedFashionItem
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


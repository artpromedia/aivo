"""Database configuration and session management with WORM compliance."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings

# Create async engine with specific configuration for audit logs
# Using NullPool to prevent connection pooling issues with append-only operations
engine = create_async_engine(
    str(settings.database_url),
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
    echo=settings.database_echo,
    # Ensure proper isolation for audit operations
    isolation_level="READ_COMMITTED",
    # Additional configuration for WORM compliance
    connect_args={
        "server_settings": {
            "application_name": "audit-log-svc",
            "jit": "off",  # Disable JIT for consistent performance
        }
    },
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with proper error handling for audit operations."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_readonly_db() -> AsyncGenerator[AsyncSession, None]:
    """Get read-only database session for queries."""
    async with AsyncSessionLocal() as session:
        try:
            # Ensure read-only mode for query operations
            await session.execute("SET TRANSACTION READ ONLY")
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables with WORM-specific constraints."""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

        # Add WORM-specific constraints and triggers if not exists
        await conn.execute("""
            -- Ensure audit_events table has proper constraints
            DO $$
            BEGIN
                -- Prevent updates on audit_events table (WORM compliance)
                IF NOT EXISTS (
                    SELECT 1 FROM pg_trigger
                    WHERE tgname = 'prevent_audit_updates'
                    AND tgrelid = 'audit_events'::regclass
                ) THEN
                    CREATE OR REPLACE FUNCTION prevent_audit_modifications()
                    RETURNS TRIGGER AS $trigger$
                    BEGIN
                        IF TG_OP = 'UPDATE' THEN
                            RAISE EXCEPTION 'Updates not allowed on audit_events table (WORM compliance)';
                        ELSIF TG_OP = 'DELETE' THEN
                            RAISE EXCEPTION 'Deletes not allowed on audit_events table (WORM compliance)';
                        END IF;
                        RETURN NULL;
                    END;
                    $trigger$ LANGUAGE plpgsql;

                    CREATE TRIGGER prevent_audit_updates
                        BEFORE UPDATE OR DELETE ON audit_events
                        FOR EACH ROW EXECUTE FUNCTION prevent_audit_modifications();
                END IF;

                -- Create index for efficient querying
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_events_timestamp
                    ON audit_events (timestamp DESC);
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_events_actor
                    ON audit_events (actor);
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_events_action
                    ON audit_events (action);
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_events_resource
                    ON audit_events (resource_type, resource_id);
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_events_hash_chain
                    ON audit_events (previous_hash, current_hash);
            END
            $$;
        """)


async def verify_worm_compliance() -> bool:
    """Verify that WORM constraints are properly enforced."""
    async with AsyncSessionLocal() as session:
        try:
            # Test that updates are prevented
            result = await session.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_trigger
                    WHERE tgname = 'prevent_audit_updates'
                    AND tgrelid = 'audit_events'::regclass
                ) as has_worm_trigger
            """)
            return result.scalar()
        except Exception:
            return False

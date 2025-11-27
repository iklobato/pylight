"""Database connection manager."""

from typing import Optional, Any
from urllib.parse import urlparse, urlunparse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from src.domain.errors import DatabaseError, ConfigurationError


class DatabaseManager:
    """Manages database connections and sessions."""

    @staticmethod
    def convertToAsyncUrl(databaseUrl: str) -> str:
        """Convert standard PostgreSQL URL to async-compatible format.

        Args:
            databaseUrl: Database connection URL string

        Returns:
            Async-compatible URL string (postgresql+asyncpg://)

        Raises:
            ConfigurationError: If URL format is invalid
        """
        if not databaseUrl or not isinstance(databaseUrl, str):
            raise ConfigurationError(
                f"Invalid database URL format: URL must be a non-empty string. Got: {type(databaseUrl).__name__}"
            )

        try:
            parsed = urlparse(databaseUrl)
        except Exception as e:
            raise ConfigurationError(
                f"Invalid database URL format: Unable to parse URL. Error: {e}"
            ) from e

        if not parsed.scheme:
            raise ConfigurationError(
                "Invalid database URL format: URL must start with 'postgresql://' or 'postgresql+asyncpg://'"
            )

        scheme = parsed.scheme.lower()

        if "+" in scheme:
            return databaseUrl

        if scheme not in ("postgresql", "postgres"):
            raise ConfigurationError(
                f"Invalid database URL format: Scheme must be 'postgresql' or 'postgres', got '{scheme}'"
            )

        if not parsed.netloc:
            raise ConfigurationError(
                "Invalid database URL format: URL must include host"
            )

        if not parsed.path or parsed.path == "/":
            raise ConfigurationError(
                "Invalid database URL format: URL must include database name"
            )

        newScheme = "postgresql+asyncpg"
        newParsed = parsed._replace(scheme=newScheme)
        return urlunparse(newParsed)

    def __init__(self, databaseUrl: str, asyncMode: bool = True) -> None:
        """Initialize database manager.

        Args:
            databaseUrl: Database connection URL
            asyncMode: Whether to use async mode (default: True)
        """
        self.asyncMode = asyncMode

        if asyncMode:
            self.databaseUrl = DatabaseManager.convertToAsyncUrl(databaseUrl)
            self.engine = create_async_engine(self.databaseUrl, echo=False)
            self.sessionMaker = async_sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
        else:
            # Convert to psycopg2 URL for sync operations
            syncUrl = databaseUrl
            if syncUrl.startswith("postgresql://") or syncUrl.startswith("postgres://"):
                syncUrl = syncUrl.replace("postgresql://", "postgresql+psycopg2://", 1).replace("postgres://", "postgresql+psycopg2://", 1)
            self.databaseUrl = syncUrl
            self.engine = create_engine(syncUrl, echo=False)
            self.sessionMaker = sessionmaker(self.engine, expire_on_commit=False)

    async def getSession(self) -> AsyncSession:
        """Get a database session.

        Returns:
            Database session

        Raises:
            DatabaseError: If session creation fails
        """
        if not self.asyncMode:
            raise DatabaseError("getSession() requires async mode")
        try:
            return self.sessionMaker()
        except Exception as e:
            raise DatabaseError(f"Failed to create database session: {e}") from e

    def sessionContext(self):
        """Get a database session context manager.

        Returns:
            Async context manager for database session

        Raises:
            DatabaseError: If async mode is not enabled
        """
        if not self.asyncMode:
            raise DatabaseError("sessionContext() requires async mode")

        class SessionContext:
            """Async context manager for database sessions."""

            def __init__(self, sessionMaker: Any) -> None:
                self.sessionMaker = sessionMaker
                self.session: Optional[AsyncSession] = None

            async def __aenter__(self) -> AsyncSession:
                """Async context manager entry.

                Returns:
                    Database session
                """
                self.session = self.sessionMaker()
                return self.session

            async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
                """Async context manager exit.

                Args:
                    exc_type: Exception type
                    exc_val: Exception value
                    exc_tb: Exception traceback
                """
                if self.session:
                    await self.session.close()

        return SessionContext(self.sessionMaker)

    def getSyncSession(self):
        """Get a synchronous database session.

        Returns:
            Synchronous database session

        Raises:
            DatabaseError: If session creation fails
        """
        if self.asyncMode:
            raise DatabaseError("getSyncSession() requires sync mode")
        return self.sessionMaker()

    async def close(self) -> None:
        """Close database connections."""
        if self.asyncMode:
            await self.engine.dispose()
        else:
            self.engine.dispose()


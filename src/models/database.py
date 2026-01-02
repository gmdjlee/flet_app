"""Database configuration and utilities."""

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def get_default_db_path() -> Path:
    """Get the default database path in user's app data directory."""
    import platform

    system = platform.system()
    if system == "Windows":
        app_data = Path.home() / "AppData" / "Local" / "dart-db-flet"
    elif system == "Darwin":  # macOS
        app_data = Path.home() / "Library" / "Application Support" / "dart-db-flet"
    else:  # Linux and others
        app_data = Path.home() / ".local" / "share" / "dart-db-flet"

    app_data.mkdir(parents=True, exist_ok=True)
    return app_data / "dart-db.sqlite"


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable WAL mode and foreign keys for SQLite connections."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_engine(db_path: str | None = None) -> Engine:
    """Create and return a SQLAlchemy engine.

    Args:
        db_path: Path to SQLite database file. Use ":memory:" for in-memory database.
                 If None, uses the default app data path.

    Returns:
        SQLAlchemy Engine instance.
    """
    if db_path is None:
        db_path = str(get_default_db_path())
    elif db_path != ":memory:":
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    url = f"sqlite:///{db_path}" if db_path != ":memory:" else "sqlite:///:memory:"
    return create_engine(url, echo=False, pool_pre_ping=True)


def get_session(engine: Engine) -> Session:
    """Create and return a new database session.

    Args:
        engine: SQLAlchemy Engine instance.

    Returns:
        SQLAlchemy Session instance.
    """
    session_factory = sessionmaker(bind=engine)
    return session_factory()


def init_db(db_path: str | None = None) -> Engine:
    """Initialize the database and create all tables.

    Args:
        db_path: Path to SQLite database file. Use ":memory:" for in-memory database.
                 If None, uses the default app data path.

    Returns:
        SQLAlchemy Engine instance.
    """
    # Import models to register them with Base
    from src.models.corporation import Corporation  # noqa: F401
    from src.models.filing import Filing  # noqa: F401
    from src.models.financial_statement import FinancialStatement  # noqa: F401

    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine

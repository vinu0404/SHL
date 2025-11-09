from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from app.models.database_models import Base
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("sqlite_db")


class SQLiteDatabase:
    """SQLite database manager"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.SQLITE_DB_PATH
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    def initialize(self):
        """Initialize database connection and create tables"""
        if self._initialized:
            logger.info("Database already initialized")
            return
        
        try:
            # Ensure directory exists
            db_file = Path(self.db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create engine
            self.engine = create_engine(
                f"sqlite:///{self.db_path}",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            
            self._initialized = True
            logger.info(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get database session with context manager"""
        if not self._initialized:
            self.initialize()
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_db_session(self) -> Session:
        """Get database session for dependency injection"""
        if not self._initialized:
            self.initialize()
        
        db = self.SessionLocal()
        try:
            return db
        except Exception as e:
            db.close()
            raise
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")
    
    def drop_all_tables(self):
        """Drop all tables (use with caution)"""
        if self.engine:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
    
    def recreate_tables(self):
        """Drop and recreate all tables"""
        self.drop_all_tables()
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables recreated")


# Global database instance
db_manager = SQLiteDatabase()


def get_db():
    """Dependency for FastAPI to get database session"""
    db = db_manager.get_db_session()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database on startup"""
    db_manager.initialize()
    logger.info("Database initialization complete")


async def close_db():
    """Close database on shutdown"""
    db_manager.close()
    logger.info("Database closed")
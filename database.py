# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# In production, this URL must be hidden in a .env file
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:aakarsh111@localhost:5433/marketplace"

# The engine manages the actual connections to PostgreSQL
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# SessionLocal spawns individual database conversations per web request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency Injection: Provides a safe database session to our API routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
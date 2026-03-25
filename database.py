from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

# ================================
# 🔐 LOAD ENV VARIABLES
# ================================
load_dotenv()

# ================================
# 🌐 GET DATABASE URL
# ================================
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# ================================
# 🧠 ENGINE SETUP (POSTGRES + SQLITE FALLBACK)
# ================================
if not SQLALCHEMY_DATABASE_URL:
    print("⚠️ DATABASE_URL not found. Using SQLite (local dev).")

    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}  # required for SQLite
    )

else:
    print(f"✅ Using Database: {SQLALCHEMY_DATABASE_URL}")

    # Fix for Render / Railway
    if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
            "postgres://", "postgresql://"
        )

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )

# ================================
# 🗄️ SESSION CONFIG
# ================================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ================================
# 🧱 BASE MODEL
# ================================
Base = declarative_base()

# ================================
# 🔌 DB DEPENDENCY (FASTAPI)
# ================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
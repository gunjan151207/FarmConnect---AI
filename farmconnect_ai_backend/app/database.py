import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Locate existing farmer_marketplace.db
CANDIDATE_PATHS = [
    DATA_DIR / "farmer_marketplace.db",
    BASE_DIR / "farmer_marketplace.db",
    BASE_DIR.parent / "farmer_marketplace.db",
    Path(r"c:\Users\user\Downloads\farmer_marketplace_backend\farmer_marketplace.db")
]

DB_PATH = None
for p in CANDIDATE_PATHS:
    if p.exists():
        DB_PATH = p
        break

if not DB_PATH:
    DB_PATH = DATA_DIR / "farmer_marketplace.db"

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



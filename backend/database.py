from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# =========================
# CONFIGURACIÓN DB
# =========================

DATABASE_URL = "sqlite:///./barberia.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Necesario para SQLite
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# =========================
# DEPENDENCIA FASTAPI
# =========================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

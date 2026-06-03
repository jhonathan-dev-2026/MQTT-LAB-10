# backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator

# Usamos SQLite local para el entorno de desarrollo industrial
DATABASE_URL = "sqlite:///./smat_industrial.db"

# Engine configurado para manejar múltiples hilos de ejecución de forma segura
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Factoría de sesiones vinculada a nuestro motor
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para la declaración de modelos ORM
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency Provider para el ciclo de vida de la base de datos.
    Garantiza el cierre automático de la conexión tras cada transacción.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
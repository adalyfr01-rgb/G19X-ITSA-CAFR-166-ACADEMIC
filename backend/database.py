import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Leer DATABASE_URL estrictamente desde el archivo .env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "ERROR CRÍTICO: La variable DATABASE_URL no está configurada en el archivo .env\n"
        "Crea o verifica el archivo .env dentro de la carpeta backend/ con la siguiente estructura:\n"
        "DATABASE_URL=postgresql://postgres:tu_password@localhost:5433/capacitacion_db"
    )

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
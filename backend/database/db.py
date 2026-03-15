from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", 3306)
DB_USE_PURE = os.getenv("DB_USE_PURE", True)
DB_AUTH_PLUGIN = os.getenv("DB_AUTH_PLUGIN", 'mysql_native_password')
DB_CHARSET = os.getenv("DB_CHARSET", 'utf8mb4')
DB_AUTOCOMMIT = os.getenv("DB_AUTOCOMMIT", True)
DB_CONNECTION_TIMEOUT = os.getenv("DB_CONNECTION_TIMEOUT", 30)

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency pour obtenir une session de base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
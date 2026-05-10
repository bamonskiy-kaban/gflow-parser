from sqlalchemy.orm import declarative_base, sessionmaker

from sqlalchemy import create_engine

from config import API_DB_POSTGRES_URL

engine = create_engine(API_DB_POSTGRES_URL)
SessionLocal = sessionmaker(autoflush=False, bind=engine)
Base = declarative_base()

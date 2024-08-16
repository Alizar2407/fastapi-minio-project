from .db_config import db_settings

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = db_settings.DATABASE_CONNECTION_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)

session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

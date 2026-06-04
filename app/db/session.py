import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://fund_lab:fund_lab@localhost:5432/fund_lab")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

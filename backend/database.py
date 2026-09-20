from sqlmodel import SQLModel, create_engine, Session
from config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

def get_session():
    with Session(engine) as session:
        yield session
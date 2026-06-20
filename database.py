from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./blog.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass

# get_db is a dependency function that provides sessions to our routes
# fastapi's dependency injection calls this function for every request
def get_db():
    with SessionLocal() as db:
        yield db
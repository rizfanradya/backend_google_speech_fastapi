from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from .config import (
    DB_HOSTNAME as DBH,
    DB_NAME as DBN,
    DB_PASSWORD as DBP,
    DB_PORT as DBPRT,
    DB_USER as DBU
)

DATABASE_URL = f"postgresql+asyncpg://{DBU}:{DBP}@{DBH}:{DBPRT}/{DBN}"

db_engine = create_async_engine(DATABASE_URL, future=True)

SessionLocal = sessionmaker(
    db_engine,
    expire_on_commit=False,
    class_=AsyncSession
)

Base = declarative_base()


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()

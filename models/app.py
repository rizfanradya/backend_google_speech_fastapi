from utils.database import Base
from sqlalchemy.schema import Column
from sqlalchemy.types import String, Integer, Text


class App(Base):
    __tablename__ = "app"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(length=255), nullable=False)
    project_id = Column(Text)
    api_key = Column(Text)

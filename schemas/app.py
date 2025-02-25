from pydantic import BaseModel
from typing import List


class AppSchema(BaseModel):
    name: str
    project_id: str
    api_key: str

    class Config:
        from_attributes = True


class BaseSchema(AppSchema):
    id: int

    class Config:
        from_attributes = True


class AppResponseSchema(BaseModel):
    total_data: int
    data: List[BaseSchema]

    class Config:
        from_attributes = True

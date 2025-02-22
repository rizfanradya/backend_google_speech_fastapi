from fastapi import APIRouter, Depends
from utils.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from utils.auth import TokenAuthorization
from utils.error_response import send_error_response
from utils.redis import redis
from utils.config import CACHE_EXPIRED
from sqlalchemy import or_, cast, String, func
from sqlalchemy.future import select
import json
from models.role import Role as BaseModel
from schemas.role import (
    RoleSchema as MainBaseSchema,
    RoleResponseSchema as GetAllSchema,
    BaseSchema,
)

router = APIRouter()
title = 'role'
msg_not_found = 'Role Not Found'
msg_already_exist = 'Role Already Exist'


@router.post('/_create')
async def create(data: MainBaseSchema, session: AsyncSession = Depends(get_db), token: str = Depends(TokenAuthorization)):
    try:
        add_db = BaseModel(**data.dict())
        session.add(add_db)
        await session.commit()
        await session.refresh(add_db)
        return add_db
    except Exception as error:
        send_error_response(str(error), msg_already_exist)


@router.put('/_update')
async def update(id: int, data: MainBaseSchema, session: AsyncSession = Depends(get_db), token: str = Depends(TokenAuthorization)):
    result = await session.execute(select(BaseModel).where(BaseModel.id == int(id)))
    data_info = result.scalars().first()
    if data_info is None:
        send_error_response(msg_not_found)
    try:
        await redis.delete(f"{title}:{id}")
        for key, value in data.dict().items():
            if value is not None:
                setattr(data_info, key, value)
        await session.commit()
        await session.refresh(data_info)
        return data_info
    except Exception as error:
        send_error_response(str(error), msg_already_exist)


@router.get('/_get_all', response_model=GetAllSchema)
async def get_all(limit: int = 10, offset: int = 0, session: AsyncSession = Depends(get_db), token: str = Depends(TokenAuthorization)):
    total_data = await session.execute(select(func.count()).select_from(BaseModel))
    result = await session.execute(select(BaseModel).offset(offset).limit(limit))
    return {
        "total_data": total_data.scalar(),
        "data": result.scalars().all()
    }


@router.get('/_search', response_model=GetAllSchema)
async def search(search: str, session: AsyncSession = Depends(get_db), token: str = Depends(TokenAuthorization)):
    query = await session.execute(select(BaseModel).filter(or_(*[
        cast(getattr(BaseModel, column), String).ilike(f"%{search}%")
        if getattr(BaseModel, column).type.python_type == str
        else cast(getattr(BaseModel, column), String).ilike(f"%{search}%")
        for column in BaseModel.__table__.columns.keys()
    ])))

    total_data = await session.execute(select(func.count()).select_from(BaseModel))
    total_data = total_data.scalar()

    return {
        "total_data": total_data,
        "data": query.scalars().all()
    }


@router.get("/_get_id", response_model=BaseSchema)
async def get_by_id(id: int, session: AsyncSession = Depends(get_db), token: str = Depends(TokenAuthorization)):
    try:
        cache_key = f"{title}:{id}"
        cached_data = await redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)

        query = await session.execute(select(BaseModel).where(BaseModel.id == int(id)))
        query = query.scalars().first()
        if query is None:
            send_error_response(msg_not_found)

        result = BaseSchema.model_validate(query).model_dump()
        await redis.set(cache_key, json.dumps(result), ex=CACHE_EXPIRED)
        return result
    except Exception as error:
        send_error_response(str(error), msg_not_found)


@router.delete('/_delete')
async def delete(id: int, session: AsyncSession = Depends(get_db), token: str = Depends(TokenAuthorization)):
    try:
        result = await session.execute(select(BaseModel).where(BaseModel.id == int(id)))
        query = result.scalars().first()
        if query:
            await redis.delete(f"{title}:{id}")
            await session.delete(query)
            await session.commit()
    except Exception as error:
        send_error_response(str(error), 'Cannot delete this data')

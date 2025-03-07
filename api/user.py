from fastapi import APIRouter, Depends
from utils.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from utils.auth import TokenAuthorization
from utils.error_response import send_error_response
from utils.hashed_password import hashed_password
from utils.redis import redis
from utils.config import CACHE_EXPIRED
from sqlalchemy import or_, cast, String, func
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
import json
from models.role import Role as RoleModel
from models.user import User as BaseModel
from schemas.user import (
    UserSchema as MainBaseSchema,
    UserResponseSchema as GetAllSchema,
    MainBaseSchemaCreate,
    BaseSchema
)

router = APIRouter()
title = 'user'
msg_not_found = 'User Not Found'
msg_already_exist = 'User already exists or role id not found'


@router.post('/_create')
async def create(data: MainBaseSchemaCreate, session: AsyncSession = Depends(get_db)):
    data.password = hashed_password(data.password)

    try:
        admin_role_id = 0
        query_admin_role = await session.execute(select(RoleModel).where(RoleModel.role.ilike("admin")))
        admin_role = query_admin_role.scalars().first()
        if admin_role is None:
            add_admin_role = RoleModel()
            add_admin_role.role = "admin"
            session.add(add_admin_role)
            await session.commit()
            await session.refresh(add_admin_role)
            admin_role_id = add_admin_role.id
        else:
            admin_role_id = admin_role.id

        name_parts = data.full_name.strip().split()
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        add_db = BaseModel()
        add_db.email = data.email
        add_db.password = data.password
        add_db.first_name = first_name
        add_db.last_name = last_name
        add_db.role_id = admin_role_id
        add_db.is_active = True

        session.add(add_db)
        await session.commit()
        await session.refresh(add_db)

        add_db.username = f"{data.email.split('@')[0]}{add_db.id}"
        await session.commit()
        await session.refresh(add_db)

        return add_db
    except Exception as error:
        send_error_response(str(error), msg_already_exist)


@router.get('/_get_all', response_model=GetAllSchema)
async def get_all(limit: int = 10, offset: int = 0, session: AsyncSession = Depends(get_db), token: str = Depends(TokenAuthorization)):
    result = await session.execute(select(BaseModel).options(joinedload(BaseModel.role)).offset(offset).limit(limit))
    total_data = await session.execute(select(func.count()).select_from(BaseModel))
    return {
        "total_data": total_data.scalar(),
        "data": result.scalars().all()
    }


@router.get('/_search', response_model=GetAllSchema)
async def search(search: str, session: AsyncSession = Depends(get_db), token: str = Depends(TokenAuthorization)):
    query = await session.execute(select(BaseModel).options(joinedload(BaseModel.role)).filter(or_(*[
        cast(getattr(BaseModel, column), String).ilike(f"%{search}%")
        if getattr(BaseModel, column).type.python_type == str
        else cast(getattr(BaseModel, column), String).ilike(f"%{search}%")
        for column in BaseModel.__table__.columns.keys()
    ])))
    total_data = await session.execute(select(func.count()).select_from(BaseModel))
    return {
        "total_data": total_data.scalar(),
        "data": query.scalars().all()
    }


@router.get("/_get_id", response_model=BaseSchema)
async def get_by_id(id: int, session: AsyncSession = Depends(get_db)):
    try:
        cache_key = f"{title}:{id}"
        cached_data = await redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)

        query = await session.execute(select(BaseModel).options(joinedload(BaseModel.role)).where(BaseModel.id == int(id)))
        query = query.scalars().first()
        if query is None:
            send_error_response(msg_not_found)

        result = BaseSchema.model_validate(query).model_dump()
        await redis.set(cache_key, json.dumps(result), ex=CACHE_EXPIRED)
        return result
    except Exception as error:
        send_error_response(str(error), msg_not_found)


@router.put('/_update')
async def update(id: int, data: MainBaseSchema, session: AsyncSession = Depends(get_db), token: str = Depends(TokenAuthorization)):
    data.password = hashed_password(data.password)
    result = await session.execute(select(BaseModel).where(BaseModel.id == int(id)))
    data_info = result.scalars().first()
    if data_info is None:
        send_error_response(msg_not_found)
    try:
        await redis.delete(f"{title}:{id}")
        await redis.delete(f"{title}:{data_info.email}")
        for key, value in data.dict().items():
            if value is not None:
                setattr(data_info, key, value)
        await session.commit()
        await session.refresh(data_info)
        return data_info
    except Exception as error:
        send_error_response(str(error), msg_already_exist)


@router.delete('/_delete')
async def delete(id: int, session: AsyncSession = Depends(get_db), token: str = Depends(TokenAuthorization)):
    try:
        result = await session.execute(select(BaseModel).where(BaseModel.id == int(id)))
        query = result.scalars().first()
        if query:
            await redis.delete(f"{title}:{id}")
            await redis.delete(f"{title}:{query.email}")
            await session.delete(query)
            await session.commit()
    except Exception as error:
        send_error_response(str(error), 'Cannot delete this data')

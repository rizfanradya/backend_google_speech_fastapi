from fastapi import APIRouter, Depends
from utils.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from utils.auth import TokenAuthorization
from utils.error_response import send_error_response
from typing import Optional
from sqlalchemy import or_, cast, String, func
from models.role import Role
from schemas.role import RoleSchema, RoleResponseSchema
from sqlalchemy.future import select

router = APIRouter()


@router.post('/role')
async def create_role(role: RoleSchema, session: AsyncSession = Depends(get_db), token: str = Depends(TokenAuthorization)):
    try:
        new_data = Role(**role.dict())
        session.add(new_data)
        await session.commit()
        await session.refresh(new_data)
        return new_data
    except Exception as error:
        send_error_response(str(error), 'role already exist')


@router.put('/role/{id}')
async def update_role(id: int, role: RoleSchema, session: AsyncSession = Depends(get_db), token: str = Depends(TokenAuthorization)):
    result = await session.execute(select(Role).where(Role.id == int(id)))
    data_info = result.scalars().first()
    if data_info is None:
        send_error_response('Data not found')
    try:
        for key, value in role.dict().items():
            if value is not None:
                setattr(data_info, key, value)
        await session.commit()
        await session.refresh(data_info)
        return data_info
    except Exception as error:
        send_error_response(str(error), 'role already exist')


@router.get('/role', response_model=RoleResponseSchema)
async def get_role(limit: int = 10, offset: int = 0, search: Optional[str] = None, role_id: Optional[int] = None, session: AsyncSession = Depends(get_db), token: str = Depends(TokenAuthorization)):
    query = select(Role)
    if role_id:
        query = query.where(Role.id == int(role_id))
    if search:
        query = query.filter(or_(*[
            cast(getattr(Role, column), String).ilike(f"%{search}%")
            if getattr(Role, column).type.python_type == str
            else cast(getattr(Role, column), String).ilike(f"%{search}%")
            for column in Role.__table__.columns.keys()
        ]))
    total_data = await session.execute(select(func.count()).select_from(Role))
    total_data = total_data.scalar()

    result = await session.execute(query.offset(offset).limit(limit))
    roles = result.scalars().all()
    return {
        "total_data": total_data,
        "data": roles
    }


@router.delete('/role/{id}')
async def delete_role(id: int, session: AsyncSession = Depends(get_db), token: str = Depends(TokenAuthorization)):
    try:
        result = await session.execute(select(Role).where(Role.id == int(id)))
        data = result.scalars().first()
        if data:
            await session.delete(data)
            await session.commit()
    except Exception as error:
        send_error_response(str(error), 'Cannot delete this data')

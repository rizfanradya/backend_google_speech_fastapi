from fastapi import APIRouter, Depends
from utils.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from utils.auth import TokenAuthorization
from utils.error_response import send_error_response
from utils.hashed_password import hashed_password
from models.user import User
from schemas.user import UserSchema, UserResponseSchema
from typing import Optional
from sqlalchemy import or_, cast, String, func
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

router = APIRouter()


@router.post('/user')
async def create_user(user: UserSchema, session: AsyncSession = Depends(get_db)):
    user.password = hashed_password(user.password)
    try:
        new_user_info = User(**user.dict())
        session.add(new_user_info)
        await session.commit()
        await session.refresh(new_user_info)
        return new_user_info
    except Exception as error:
        send_error_response(
            str(error),
            'User already exists or role id not found'
        )


@router.put('/user/{id}')
async def update_user(id: int, user: UserSchema, session: AsyncSession = Depends(get_db), token: str = Depends(TokenAuthorization)):
    user.password = hashed_password(user.password)
    result = await session.execute(select(User).where(User.id == int(id)))
    user_info = result.scalars().first()
    if user_info is None:
        send_error_response('User not found')
    try:
        for key, value in user.dict().items():
            if value is not None:
                setattr(user_info, key, value)
        await session.commit()
        await session.refresh(user_info)
        return user_info
    except Exception as error:
        send_error_response(
            str(error),
            'User already exists or role id not found'
        )


@router.get('/user', response_model=UserResponseSchema)
async def get_user(limit: int = 10, offset: int = 0, search: Optional[str] = None, user_id: Optional[int] = None, session: AsyncSession = Depends(get_db)):
    query = select(User).options(joinedload(User.role))

    if user_id:
        query = query.where(User.id == int(user_id))

    if search:
        query = query.filter(or_(*[
            cast(getattr(User, column), String).ilike(f"%{search}%")
            if getattr(User, column).type.python_type == str
            else cast(getattr(User, column), String).ilike(f"%{search}%")
            for column in User.__table__.columns.keys()
        ]))

    total_data = await session.execute(select(func.count()).select_from(User))
    total_data = total_data.scalar()
    result = await session.execute(query.offset(offset).limit(limit))
    users = result.scalars().all()

    return {
        "total_data": total_data,
        "data": users
    }


@router.delete('/user/{id}')
async def delete_user(id: int, session: AsyncSession = Depends(get_db), token: str = Depends(TokenAuthorization)):
    try:
        result = await session.execute(select(User).where(User.id == int(id)))
        user = result.scalars().first()
        if user:
            await session.delete(user)
            await session.commit()
    except Exception as error:
        send_error_response(str(error), 'Cannot delete this data')

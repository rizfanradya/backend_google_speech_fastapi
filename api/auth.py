from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException
from models.user import User
import jwt
import json
import bcrypt
from datetime import timedelta, datetime
from utils.database import get_db
from utils.auth import create_access_token, create_refresh_token
from utils.error_response import send_error_response
from utils.redis import redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.future import select
from schemas.user import UserAuth as UserSchema
from utils.config import (
    JWT_REFRESH_SECRET_KEY,
    JWT_SECRET_KEY,
    ALGORITHM,
    CACHE_EXPIRED,
    ACCESS_TOKEN_MOBILE_EXPIRE_MINUTES
)

router = APIRouter()
cache_title = 'user'


@router.post("/token")
async def user_login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_db)):
    cache_key = f"{cache_title}:{form_data.username}"
    cached_data = await redis.get(cache_key)
    if cached_data:
        user_info = json.loads(cached_data)
    else:
        result = await session.execute(select(User).where(User.email == form_data.username).options(joinedload(User.role)))
        user_info = result.scalars().first()
        if user_info is None:
            send_error_response("User not found")

        user_info = UserSchema.model_validate(user_info).model_dump()
        await redis.set(cache_key, json.dumps(user_info), ex=CACHE_EXPIRED)

    user_id = int(user_info.get('id'))
    form_data_pwd = form_data.password.encode('utf-8')
    user_info_pwd = user_info.get('password').encode('utf-8')  # type: ignore
    bcrypt_checkpw = bcrypt.checkpw(form_data_pwd, user_info_pwd)
    access_token = create_access_token(user_id)  # type: ignore
    refresh_token = create_refresh_token(user_id)  # type: ignore
    if bcrypt_checkpw:
        return {
            "id": user_id,  # type: ignore
            "access_token": access_token,
            "refresh_token": refresh_token,
            "status": user_info["is_active"],  # type: ignore
            "role": user_info["role"]["role"],  # type: ignore
            "detail": "Login success"
        }
    else:
        raise HTTPException(
            status_code=404,
            detail={
                "id": user_id,  # type: ignore
                "access_token": None,
                "refresh_token": None,
                "status": False,
                "role": None,
                "detail": "Password not match"
            }
        )


@router.post("/token/mobile")
async def user_mobile_login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_db)):
    cache_key = f"{cache_title}:{form_data.username}"
    cached_data = await redis.get(cache_key)
    if cached_data:
        user_info = json.loads(cached_data)
    else:
        result = await session.execute(select(User).where(User.email == form_data.username).options(joinedload(User.role)))
        user_info = result.scalars().first()
        if user_info is None:
            send_error_response("User not found")

        user_info = UserSchema.model_validate(user_info).model_dump()
        await redis.set(cache_key, json.dumps(user_info), ex=CACHE_EXPIRED)

    user_id = int(user_info.get('id'))
    form_data_pwd = form_data.password.encode('utf-8')
    user_info_pwd = user_info.get('password').encode('utf-8')  # type: ignore
    bcrypt_checkpw = bcrypt.checkpw(form_data_pwd, user_info_pwd)

    expires_delta = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_MOBILE_EXPIRE_MINUTES)
    access_token = encoded_jwt = jwt.encode(
        payload={
            "exp": expires_delta,
            "id": user_id,
            "username": user_info['username'],
            "email": user_info['email'],
            "first_name": user_info['first_name'],
            "last_name": user_info['last_name'],
            "is_active": user_info['is_active'],
            "role": user_info['role']['role'],
        },
        key=str(JWT_SECRET_KEY),
        algorithm=ALGORITHM
    )

    if bcrypt_checkpw:
        return {
            "id": user_id,  # type: ignore
            "accessToken": access_token,
            "status": user_info["is_active"],  # type: ignore
            "role": user_info["role"]["role"],  # type: ignore
            "detail": "Login success"
        }
    else:
        raise HTTPException(
            status_code=404,
            detail={
                "id": user_id,  # type: ignore
                "accessToken": None,
                "status": False,
                "role": None,
                "detail": "Password not match"
            }
        )


@router.post("/refresh_token/{refresh_token}")
async def refresh_token(refresh_token: str, session: AsyncSession = Depends(get_db)):
    if JWT_REFRESH_SECRET_KEY is None:
        send_error_response("Environment variable JWT SECRET KEY not set")
    try:
        decode_token = jwt.decode(
            refresh_token,
            JWT_REFRESH_SECRET_KEY,  # type: ignore
            algorithms=[ALGORITHM]
        )
        user_id = int(decode_token.get('id'))

        cache_key = f"user:{user_id}"
        cached_data = await redis.get(cache_key)

        if cached_data:
            user_info = json.loads(cached_data)
        else:
            result = await session.execute(select(User).where(User.id == user_id).options(joinedload(User.role)))
            user_info = result.scalars().first()
            if user_info is None:
                send_error_response("User not found")
            user_info = UserSchema.model_validate(user_info).model_dump()
            await redis.set(cache_key, json.dumps(user_info), ex=CACHE_EXPIRED)

        user_id = int(user_info.get('id'))
        return {
            "access_token": create_access_token(user_id),  # type: ignore
            "refresh_token": create_refresh_token(user_id)  # type: ignore
        }
    except jwt.ExpiredSignatureError:
        send_error_response("Token has expired")
    except jwt.InvalidTokenError:
        send_error_response("Token is invalid")

from typing import Union, Any
from datetime import datetime, timedelta
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from .database import get_db
from .redis import redis
import json
from models.user import User
from schemas.user import BaseSchema as UserSchema
from .error_response import send_error_response
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from .config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    JWT_SECRET_KEY,
    JWT_REFRESH_SECRET_KEY,
    CACHE_EXPIRED
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")


def create_access_token(subject: Union[str, Any], expires_delta=None):
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    encoded_jwt = jwt.encode(
        payload={"exp": expires_delta, "id": str(subject)},
        key=str(JWT_SECRET_KEY),
        algorithm=ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta=None):
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    encoded_jwt = jwt.encode(
        payload={"exp": expires_delta, "id": str(subject)},
        key=str(JWT_REFRESH_SECRET_KEY),
        algorithm=ALGORITHM
    )
    return encoded_jwt


async def TokenAuthorization(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db)):
    if JWT_SECRET_KEY is None:
        send_error_response("Environment variable JWT SECRET KEY not set")
    try:
        decode_token = jwt.decode(
            token, JWT_SECRET_KEY,
            algorithms=[ALGORITHM]
        )  # type: ignore
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
            if user_info.is_active == False:
                send_error_response("Your account has not been active")

            user_info = UserSchema.model_validate(user_info).model_dump()
            await redis.set(cache_key, json.dumps(user_info), ex=CACHE_EXPIRED)

        return user_info
    except jwt.ExpiredSignatureError:
        send_error_response("Token has expired")
    except jwt.InvalidTokenError:
        send_error_response("Token is invalid")

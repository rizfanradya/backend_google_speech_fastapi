from models.user import User
from schemas.user import UserSchema
from utils.database import get_db
from utils.hashed_password import hashed_password
from models.role import Role
from schemas.role import RoleSchema
from sqlalchemy.future import select


async def data_that_must_exist_in_the_database():
    async for session in get_db():  # ✅ Gunakan async for untuk mendapatkan session
        role_admin = await session.execute(select(Role).where(Role.role == 'admin'))
        role_admin = role_admin.scalars().first()

        if not role_admin:
            role_schema = RoleSchema(role='admin')
            new_role_admin = Role(**role_schema.dict())
            session.add(new_role_admin)
            await session.commit()
            await session.refresh(new_role_admin)
            role_admin = new_role_admin

        user_admin = await session.execute(select(User).where(User.role_id == role_admin.id))
        user_admin = user_admin.scalars().first()

        if not user_admin:
            user_schema = UserSchema(
                username='rizfanradya',
                email='rizfankusuma@gmail.com',
                password=hashed_password('@Rizfan123'),
                first_name='rizfan',
                last_name='kusuma',
                role_id=role_admin.id,
                is_active=True
            )
            new_user = User(**user_schema.dict())
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

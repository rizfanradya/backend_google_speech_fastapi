from logging.config import fileConfig
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.pool import NullPool  # ✅ Tambahkan impor ini
from alembic import context
from utils.database import DATABASE_URL, Base
from models.role import *
from models.user import *

# Konfigurasi logging
config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata  # Metadata dari SQLAlchemy


def run_migrations_offline() -> None:
    """Menjalankan migrasi dalam mode offline."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Menjalankan migrasi dalam mode online dengan async engine."""
    connectable: AsyncEngine = create_async_engine(
        DATABASE_URL, poolclass=NullPool)

    async with connectable.begin() as connection:  # Menggunakan koneksi async
        # Menjalankan migrasi dalam mode sync
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()  # Menutup koneksi database setelah digunakan


def do_run_migrations(connection):
    """Konfigurasi dan jalankan migrasi."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # Menjalankan migrasi async dengan asyncio.run()
    asyncio.run(run_migrations_online())

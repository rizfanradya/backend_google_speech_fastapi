import os
import subprocess
import sys
import shutil
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from .database import DATABASE_URL


async def table_exists(conn, table_name: str) -> bool:
    result = await conn.execute(
        text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table)")
        .bindparams(table=table_name)
    )
    return result.scalar()


async def run_shell_commands():
    abs_path = os.path.abspath(__file__)
    path_dirname = os.path.dirname(abs_path)
    project_root = os.path.dirname(path_dirname)

    if os.name == 'posix':  # Linux/macOS
        python_cmd = "python3"
    elif os.name == 'nt':  # Windows
        python_cmd = "python"
    else:
        raise EnvironmentError("Unsupported operating system")

    commands = []

    versions_folder = os.path.join(project_root, 'alembic', 'versions')
    os.makedirs(versions_folder, exist_ok=True)
    if os.path.exists(versions_folder):
        for filename in os.listdir(versions_folder):
            file_path = os.path.join(versions_folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. reason: {e}")

    engine = create_async_engine(DATABASE_URL, future=True)

    async with engine.begin() as conn:
        if await table_exists(conn, 'alembic_version'):
            await conn.execute(text("TRUNCATE TABLE alembic_version RESTART IDENTITY CASCADE"))

    await engine.dispose()

    commands.extend([
        f"{python_cmd} -m alembic revision --autogenerate -m 'rev'",
        f"{python_cmd} -m alembic upgrade head"
    ])

    original_cwd = os.getcwd()
    try:
        os.chdir(project_root)
        for command in commands:
            try:
                subprocess.run(command, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Command '{command}' failed with error: {e}")
                sys.exit(1)
    finally:
        os.chdir(original_cwd)

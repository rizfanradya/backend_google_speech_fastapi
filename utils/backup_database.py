import os
import asyncio
from datetime import datetime
from .config import DB_HOSTNAME, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER
import subprocess


async def backup_database():
    MAX_BACKUPS = 3
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backup_folder = os.path.join(base_dir, "..", "data", "backups")
    os.makedirs(backup_folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_folder, f"backup_{timestamp}.sql")

    os.environ['PGPASSWORD'] = str(DB_PASSWORD)
    command = (
        f'pg_dump -h {DB_HOSTNAME} -p {DB_PORT} -U {DB_USER} -F c -b -v -f "{backup_file}" {DB_NAME}'
    )

    def run_backup():
        process = subprocess.run(
            command, shell=True, capture_output=True, text=True)
        if process.returncode == 0:
            print(f'Backup database success: {backup_file}')
        else:
            print(f"Failed backup database:\n{process.stderr}")
    await asyncio.to_thread(run_backup)

    backup_files = sorted(
        [
            os.path.join(backup_folder, f)
            for f in os.listdir(backup_folder)
            if f.endswith(".sql")
        ],
        key=os.path.getmtime
    )

    if len(backup_files) > MAX_BACKUPS:
        old_backups = backup_files[:-MAX_BACKUPS]
        for old_backup in old_backups:
            try:
                os.remove(old_backup)
            except OSError as e:
                print(f"Error deleting file {old_backup}: {e}")

    del os.environ['PGPASSWORD']

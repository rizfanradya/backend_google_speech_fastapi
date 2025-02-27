import os
from .database import get_db
from models.speech_result import SpeechResult
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession


async def check_and_remove_orphaned_files():
    print("Check and Remove Orphaned Files Start...")
    abs_path = os.path.abspath(__file__)
    base_dir = os.path.dirname(os.path.dirname(abs_path))
    async for get_session in get_db():
        session: AsyncSession = get_session

        # Check and remove orphaned uploaded files in Speech Result data
        query_db = await session.execute(
            select(SpeechResult).where(
                SpeechResult.input_file_audio.isnot(None))
        )
        data_in_db = [row.input_file_audio for row in query_db.scalars().all()]
        directory = os.path.join(
            base_dir, 'data', 'uploads', 'input_file_audio')
        os.makedirs(directory, exist_ok=True)
        files_delete = [
            f for f in os.listdir(directory) if f not in data_in_db
        ]
        for file_name in files_delete:
            file_path = os.path.join(directory, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)

        # Check and remove orphaned downloaded files in Speech Result data
        query_db = await session.execute(
            select(SpeechResult).where(
                SpeechResult.output_file_audio.isnot(None))
        )
        data_in_db = [
            row.output_file_audio for row in query_db.scalars().all()]
        directory = os.path.join(
            base_dir, 'data', 'downloads', 'output_file_audio')
        os.makedirs(directory, exist_ok=True)
        files_delete = [
            f for f in os.listdir(directory) if f not in data_in_db
        ]
        for file_name in files_delete:
            file_path = os.path.join(directory, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)

    print("Check and Remove Orphaned Files Done...")

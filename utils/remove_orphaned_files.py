import os


async def check_and_remove_orphaned_files():
    abs_path = os.path.abspath(__file__)
    base_dir = os.path.dirname(os.path.dirname(abs_path))
    # async with get_db_session() as session:

    #     Check and remove orphaned uploaded files in Masterplan data
    #     data_in_db = [file[0] for file in session.query(Masterplan.uploaded_file).where(
    #         Masterplan.uploaded_file.isnot(None)).all()]
    #     directory = os.path.join(base_dir, 'data', 'uploads')
    #     os.makedirs(directory, exist_ok=True)
    #     files_delete = [
    #         f for f in os.listdir(directory) if f not in data_in_db
    #     ]
    #     for file_name in files_delete:
    #         file_path = os.path.join(directory, file_name)
    #         if os.path.isfile(file_path):
    #             os.remove(file_path)

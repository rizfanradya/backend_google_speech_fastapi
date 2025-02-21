from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from utils.config import BACKEND_PORT
from utils.router import router
from utils.run_shell_command import run_shell_commands
from utils.data_must_exist_db import data_that_must_exist_in_the_database
from utils.remove_orphaned_files import check_and_remove_orphaned_files
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils.backup_database import backup_database
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_shell_commands()
    await data_that_must_exist_in_the_database()
    await check_and_remove_orphaned_files()
    await backup_database()
    yield


# FastAPI instance
app = FastAPI(title="App Google Speech FastAPI", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router)


# Scheduler
scheduler = AsyncIOScheduler()
scheduler.add_job(
    data_that_must_exist_in_the_database,
    'interval',
    days=1
)
scheduler.add_job(
    check_and_remove_orphaned_files,
    'interval',
    hours=1
)
scheduler.add_job(
    backup_database,
    'cron',
    hour=0,
    minute=0
)
scheduler.start()


@app.get("/")
async def root():
    await data_that_must_exist_in_the_database()
    await check_and_remove_orphaned_files()
    await backup_database()
    return {"message": app.title}


if __name__ == "__main__":
    uvicorn.run(
        "app:app", host="0.0.0.0",
        reload=True,
        port=int(BACKEND_PORT)
    )

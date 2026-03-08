"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import devices, tasks, ws
from app.database import init_db
from app.device.manager import device_manager
from app.task.engine import task_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await device_manager.start()
    await task_engine.start()
    yield
    # Shutdown
    await task_engine.stop()
    await device_manager.stop()


app = FastAPI(
    title="iPhone Device Farm",
    description="Control 5 iPhones from a Mac",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices.router)
app.include_router(tasks.router)
app.include_router(ws.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}

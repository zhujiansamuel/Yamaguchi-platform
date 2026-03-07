from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from . import tasks
from . import tasks_task2
from . import tasks_task3

app = FastAPI()

class ScrapingRequest(BaseModel):
    webhook_url: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "FastAPI server is running."}

@app.post("/run-scraping")
async def run_scraping_endpoint(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """
    Triggers the web scraping and price update task in the background.
    Optionally accepts a webhook_url to send a callback upon completion.
    """
    background_tasks.add_task(tasks.run_price_update_task, webhook_url=request.webhook_url)
    return {"message": "Scraping task started in the background."}

@app.post("/run-task2")
async def run_task2_endpoint(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """
    Triggers task2 in the background.
    Optionally accepts a webhook_url to send a callback upon completion.
    """
    background_tasks.add_task(tasks_task2.run_task2_task, webhook_url=request.webhook_url)
    return {"message": "Task2 started in the background."}

@app.post("/run-task3")
async def run_task3_endpoint(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """
    Triggers task3 in the background.
    Optionally accepts a webhook_url to send a callback upon completion.
    """
    background_tasks.add_task(tasks_task3.run_task3_task, webhook_url=request.webhook_url)
    return {"message": "Task3 started in the background."}

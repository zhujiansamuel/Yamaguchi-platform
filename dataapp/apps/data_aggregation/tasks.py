"""
Celery tasks for data_aggregation app.
All tasks here will be processed by the aggregation_queue worker.
"""
from .celery import app
import logging

logger = logging.getLogger(__name__)


@app.task(name='apps.data_aggregation.tasks.sample_aggregation_task')
def sample_aggregation_task(data):
    """
    Sample task for data aggregation.
    This is a placeholder - implement your actual aggregation logic here.
    """
    logger.info(f"Processing aggregation task with data: {data}")
    # Add your aggregation logic here
    return {"status": "completed", "result": data}


@app.task(name='apps.data_aggregation.tasks.aggregate_from_sources')
def aggregate_from_sources(source_ids):
    """
    Aggregate data from multiple sources.
    This is a placeholder - implement your actual logic here.
    """
    logger.info(f"Aggregating data from sources: {source_ids}")
    # Add your aggregation logic here
    return {"status": "completed", "sources": source_ids}

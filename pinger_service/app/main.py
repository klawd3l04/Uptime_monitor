import asyncio
from fastapi import FastAPI
from apscheduler.triggers.interval import IntervalTrigger
from app.config import logger, kafka_producer, redis_client, INTERNAL_API_KEY
from app.services.scheduler import scheduler, sync_monitors, active_jobs

app = FastAPI(title="Pinger Engine")

@app.on_event("startup")
async def startup_event():
    """
    Bootstrap process for the service.
    
    1. Starts the async scheduler.
    2. Registers a recurring job to sync monitor definitions from the source-of-truth.
    3. Triggers an immediate first sync to start working without delay.
    """
    logger.info("Starting Pinger Engine infrastructure...")
    
    # Internal API key check for early failure if configuration is missing
    if not INTERNAL_API_KEY:
        logger.warning("INTERNAL_API_KEY is not set. Service-to-Service communication will fail.")

    scheduler.start()
    
    # Monitors are checked for updates every minute
    scheduler.add_job(
        sync_monitors, 
        IntervalTrigger(seconds=60), 
        id="sync_monitors_task",
        replace_existing=True
    )
    
    # Run the first sync in the background so it doesn't block app boot
    asyncio.create_task(sync_monitors())

@app.get("/health")
def health():
    """
    Basic health check for Kubernetes or load balancers.
    Provides a quick overview of the service's internal state and connectivity.
    """
    return {
        "status": "healthy", 
        "version": "1.5.2",
        "jobs_active": len(active_jobs),
        "infrastructure": {
            "kafka": kafka_producer is not None, 
            "redis": redis_client is not None
        }
    }

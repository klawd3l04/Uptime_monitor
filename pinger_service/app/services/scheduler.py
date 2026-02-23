import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.config import logger, USER_SERVICE_URL, INTERNAL_API_KEY
from app.services.pinger import ping_url

# Global scheduler for async tasks
scheduler = AsyncIOScheduler()
# Keep track of jobs to avoid duplicates and handle cleanup
active_jobs = {} # { monitor_id: job_object }

async def sync_monitors():
    """
    Sync local scheduler with current monitors from the User Service.
    
    This picks up new monitors, stops removed ones, and uses a shared
    internal key for security.
    """
    logger.info("Syncing active monitors from core...")
    try:
        headers = {"X-Internal-API-Key": INTERNAL_API_KEY}
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{USER_SERVICE_URL}/all_monitors", headers=headers)
            
            if response.status_code == 200:
                monitors = response.json()
                current_ids = set()
                
                for m in monitors:
                    m_id = str(m['id'])
                    m_url = m['url']
                    m_interval = m.get('interval_seconds', 60)
                    current_ids.add(m_id)
                    
                    # Add new jobs if they aren't already running
                    if m_id not in active_jobs:
                        logger.info(f"Adding new monitoring job: {m_url} (Interval: {m_interval}s)")
                        job = scheduler.add_job(
                            ping_url, 
                            IntervalTrigger(seconds=m_interval),
                            args=[m['id'], m_url, m_interval],
                            id=m_id
                        )
                        active_jobs[m_id] = job
                
                # Remove jobs for monitors that are no longer active
                for old_id in list(active_jobs.keys()):
                    if old_id not in current_ids:
                        logger.info(f"Monitor {old_id} is no longer active. Deleting job.")
                        try:
                            scheduler.remove_job(old_id)
                        except Exception:
                            # Job might be gone already
                            pass
                        del active_jobs[old_id]
            else:
                logger.error(f"Failed to sync monitors. Status: {response.status_code}")
                    
    except Exception as e:
        # Connection errors are logged; retrying on the next cycle
        logger.error(f"Internal sync error: {e}")

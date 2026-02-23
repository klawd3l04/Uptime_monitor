import httpx
import json
from datetime import datetime
from app.config import logger, redis_client, kafka_producer, KAFKA_TOPIC

async def ping_url(monitor_id: int, url: str, interval: int):
    """
    Check the health of a target URL.
    
    Uses a Redis lock to ensure only one pinger instance handles a given 
    monitor at a time when scaled horizontally.
    """
    lock_key = f"lock:pinger:{monitor_id}"
    
    if redis_client:
        # Lock TTL is slightly shorter than the check interval
        lock_ttl = max(5, interval - 1)
        if not redis_client.set(lock_key, "active", ex=lock_ttl, nx=True):
            logger.debug(f"Monitor {monitor_id} is already being handled. Skipping.")
            return

    start_time = datetime.utcnow()
    status_code = None
    is_up = False
    error = None
    
    logger.info(f"Pinging {url}...")
    try:
        # Use a timeout and custom User-Agent to avoid generic filters
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            headers = {'User-Agent': 'UptimeMonitor-Engine/1.5'}
            response = await client.get(url, headers=headers)
            status_code = response.status_code
            is_up = 200 <= status_code < 400
    except httpx.TimeoutException:
        error = "Network timeout"
    except Exception as e:
        # Capture any other network-related failures
        error = str(e)
    
    end_time = datetime.utcnow()
    latency_ms = int((end_time - start_time).total_seconds() * 1000)
    
    result = {
        "monitor_id": monitor_id,
        "url": url,
        "timestamp": start_time.isoformat(),
        "is_up": is_up,
        "status_code": status_code,
        "latency_ms": latency_ms,
        "error": error
    }
    
    # Push results to Kafka
    if kafka_producer:
        try:
            kafka_producer.produce(
                KAFKA_TOPIC, 
                key=str(monitor_id), 
                value=json.dumps(result)
            )
            # Poll(0) to serve existing delivery reports without blocking the next ping
            kafka_producer.poll(0)
        except Exception as e:
            logger.error(f"Failed to publish result to Kafka for {monitor_id}: {e}")

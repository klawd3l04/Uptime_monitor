import requests
import time
from app.config import logger, INTERNAL_API_KEY

def api_call_internal(method: str, url: str, json_data: dict) -> bool:
    """
    Execute an authenticated internal API request to the User Service.
    
    Includes a basic retry loop to handle temporary network issues within 
    the cluster.
    """
    headers = {"X-Internal-API-Key": INTERNAL_API_KEY}
    for i in range(3):
        try:
            # Short timeout to avoid blocking the processing pipeline
            res = requests.request(method, url, json=json_data, headers=headers, timeout=5)
            if res.status_code < 300:
                return True
            else:
                logger.warning(f"Internal API error {res.status_code} for {url}: {res.text}")
        except Exception as e:
            logger.warning(f"API attempt {i+1} failed for {url}: {e}")
            time.sleep(1)
    
    logger.error(f"Internal API call failed after 3 attempts: {url}")
    return False

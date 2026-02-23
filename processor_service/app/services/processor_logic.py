import json
from app.config import (
    logger, redis_client, alert_producer, 
    USER_SERVICE_URL, KAFKA_ALERTS_TOPIC
)
from app.services.api import api_call_internal

def update_uptime_stats(monitor_id: int, is_up: bool):
    """
    Sync the latest check result with the centralized database.
    
    Stats calculation is delegated to the User Service to maintain a 
    single source of truth.
    """
    url = f"{USER_SERVICE_URL}/monitors/{monitor_id}/stats"
    api_call_internal("POST", url, {"is_up": is_up})

def handle_state_transition(monitor_id: int, is_up: bool, data: dict):
    """
    Evaluate results and detect state changes (UP <-> DOWN).
    
    Stored state in Redis ensures that incidents and alerts are only 
    triggered once per transition.
    """
    event_type = "UP" if is_up else "DOWN"
    state_key = f"monitor:{monitor_id}:state"
    
    if not redis_client:
        logger.error(f"Redis unavailable; cannot process transition for {monitor_id}.")
        return

    last_state = redis_client.get(state_key)
    
    # Act only if state has changed to prevent duplicate alerts
    if last_state != event_type:
        # 1. Log transition to Postgres for the audit trail
        url = f"{USER_SERVICE_URL}/monitors/{monitor_id}/incidents"
        details = data.get('error', 'N/A')
        
        if api_call_internal("POST", url, {"event_type": event_type, "details": details}):
            # 2. Update state in Redis
            redis_client.set(state_key, event_type)
            logger.info(f"Transition for monitor {monitor_id}: {last_state} -> {event_type}")

            # 3. Emit alert event to Kafka for downstream notifications
            alert_payload = {
                "monitor_id": monitor_id,
                "url": data['url'],
                "event_type": event_type,
                "status_code": data.get('status_code'),
                "latency_ms": data.get('latency_ms'),
                "error": details,
                "timestamp": data.get('timestamp')
            }
            
            if alert_producer:
                try:
                    alert_producer.produce(
                        KAFKA_ALERTS_TOPIC, 
                        key=str(monitor_id), 
                        value=json.dumps(alert_payload)
                    )
                    alert_producer.poll(0)
                except Exception as e:
                    logger.error(f"Failed to publish alert to Kafka for {monitor_id}: {e}")

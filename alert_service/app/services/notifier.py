import requests
from app.config import logger, SLACK_WEBHOOK_URL

def send_slack_notification(message: str):
    """
    Format and send a notification to a Slack channel.
    """
    if not SLACK_WEBHOOK_URL:
        # Avoid crashing if the webhook isn't configured
        logger.warning(f"Notification skipped: No Slack Webhook configured. Message: {message}")
        return
    
    try:
        payload = {"text": message}
        # 10s timeout to prevent hanging the worker on Slack outages
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Slack notification dispatched successfully.")
    except Exception as e:
        logger.error(f"Failed to transmit Slack alert: {e}")

def handle_alert_event(data: dict):
    """
    Convert a raw Kafka alert event into a user-friendly notification.
    
    Emojis and markdown are used to improve readability on Slack clients.
    """
    url = data.get('url', 'Unknown URL')
    event_type = data.get('event_type')
    status_code = data.get('status_code', 'N/A')
    latency = data.get('latency_ms', 'N/A')
    error_details = data.get('error', 'N/A')
    
    if event_type == "DOWN":
        msg = (
            f"🚨 *MONITOR CRITICAL: Site is DOWN!* 🚨\n"
            f"*URL:* {url}\n"
            f"*Status Code:* {status_code}\n"
            f"*Latency:* {latency}ms\n"
            f"*Error Details:* {error_details}"
        )
    else:
        # Recognition of recovery is just as important as the downtime alert
        msg = (
            f"✅ *MONITOR RECOVERY: Site back ONLINE!* ✅\n"
            f"*URL:* {url}\n"
            f"*Latency:* {latency}ms"
        )
    
    send_slack_notification(msg)

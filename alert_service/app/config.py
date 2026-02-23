import os
import logging

# Basic logging configuration for consistency
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AlertService")

# Infrastructure & Integration Settings
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "kafka:9092")
KAFKA_ALERTS_TOPIC = "monitoring-alerts"
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

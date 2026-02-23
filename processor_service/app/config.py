import os
import redis
import logging
from confluent_kafka import Producer

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ProcessorService")

# Infrastructure settings
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "kafka:9092")
KAFKA_RESULTS_TOPIC = "monitoring-results"
KAFKA_ALERTS_TOPIC = "monitoring-alerts" 
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
USER_SERVICE_URL = os.environ.get("USER_SERVICE_URL", "http://user_service:5000")
INTERNAL_API_KEY = os.environ.get("INTERNAL_API_KEY")

def get_redis_client():
    """Initializes and returns a Redis client."""
    try:
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        # Verify connection immediately
        client.ping()
        return client
    except Exception as e:
        logger.error(f"Redis initialization failed: {e}")
        return None

def get_alert_producer():
    """Returns a Kafka producer configured for alert emissions."""
    conf = {'bootstrap.servers': KAFKA_BROKER, 'acks': 'all'}
    try:
        return Producer(**conf)
    except Exception as e:
        logger.error(f"Kafka producer initialization failed: {e}")
        return None

redis_client = get_redis_client()
alert_producer = get_alert_producer()

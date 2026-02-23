import os
import redis
from confluent_kafka import Producer
import logging

# Basic configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PingerService")

# Config & Infrastructure
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = "monitoring-results"
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
USER_SERVICE_URL = os.environ.get("USER_SERVICE_URL", "http://user_service:5000")
INTERNAL_API_KEY = os.environ.get("INTERNAL_API_KEY")

# Redis client for distributed locking
def get_redis_client():
    """
    Establish a Redis connection. Ping the server to verify connectivity.
    """
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.ping()
        logger.info(f"Connected to Redis at {REDIS_HOST}")
        return r
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return None

# Kafka Producer for streaming results
def get_kafka_producer():
    """
    Initializes a Kafka producer with high reliability settings.
    """
    producer_conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'client.id': 'pinger-service-v1.5',
        'acks': 'all',
        'retries': 5,
        'retry.backoff.ms': 500
    }
    try:
        p = Producer(**producer_conf)
        logger.info(f"Connected to Kafka at {KAFKA_BROKER}")
        return p
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        return None

redis_client = get_redis_client()
kafka_producer = get_kafka_producer()

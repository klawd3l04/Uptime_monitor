from confluent_kafka import Consumer, KafkaError
import json
import time
from app.config import (
    logger, KAFKA_BROKER, KAFKA_RESULTS_TOPIC, redis_client
)
from app.services.processor_logic import update_uptime_stats, handle_state_transition

def consume_results():
    """
    Main ingestion loop for monitoring results.
    
    Kafka processes health checks asynchronously, decoupling 
    pinger output from database writes.
    """
    conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': 'processor-group-v1.6', 
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': True
    }
    
    consumer = None
    # Retry Kafka connection to handle broker startup
    for i in range(20):
        try:
            consumer = Consumer(conf)
            consumer.subscribe([KAFKA_RESULTS_TOPIC])
            logger.info(f"Subscribed to topic: {KAFKA_RESULTS_TOPIC}")
            break
        except Exception as e:
            logger.warning(f"Kafka unavailable ({i+1}): {e}. Retrying in 5s...")
            time.sleep(5)
    
    if not consumer:
        logger.error("Could not connect to Kafka. Shutting down.")
        return

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error(f"Kafka stream error: {msg.error()}")
                continue

            try:
                # Decode JSON result from the pinger
                data = json.loads(msg.value().decode('utf-8'))
                monitor_id = data.get('monitor_id')
                is_up = data.get('is_up')
                
                if monitor_id is None:
                    continue

                # 1. Update long-term aggregate stats in the DB
                update_uptime_stats(monitor_id, is_up)
                
                # 2. Check for state transitions and trigger alerts
                handle_state_transition(monitor_id, is_up, data)

                # 3. Cache real-time status and history for the dashboard
                if redis_client:
                    raw_val = msg.value().decode('utf-8')
                    redis_client.set(f"monitor:{monitor_id}:status", raw_val)
                    redis_client.lpush(f"monitor:{monitor_id}:history", raw_val)
                    # Keep only the last 20 results for sparkline charts
                    redis_client.ltrim(f"monitor:{monitor_id}:history", 0, 19)

            except Exception as e:
                logger.error(f"Failed to process message for monitor {data.get('monitor_id')}: {e}")

    finally:
        # Ensure offsets are committed on shutdown
        consumer.close()

if __name__ == "__main__":
    # Delay to allow infrastructure (Kafka/Redis) to settle in dev environments
    time.sleep(5)
    consume_results()

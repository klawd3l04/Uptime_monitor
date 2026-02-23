from confluent_kafka import Consumer, KafkaError
import json
import time
from app.config import logger, KAFKA_BROKER, KAFKA_ALERTS_TOPIC
from app.services.notifier import handle_alert_event

def run_alert_worker():
    """
    Main worker loop for alert processing.
    
    Subscribes to the 'monitoring-alerts' topic to handle pre-filtered 
    incident events.
    """
    logger.info(f"Alert Worker initializing. Group: alert-service-v1.6")
    
    conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': 'alert-service-group-v1.6',
        'auto.offset.reset': 'latest',
        'enable.auto.commit': True
    }
    
    consumer = None
    # Wait for Kafka to become available
    for i in range(20):
        try:
            consumer = Consumer(conf)
            consumer.subscribe([KAFKA_ALERTS_TOPIC])
            logger.info(f"Alert Service online and listening to: {KAFKA_ALERTS_TOPIC}")
            break
        except Exception as e:
            logger.warning(f"Kafka unavailable for Alerting ({i+1}): {e}. Retrying in 5s...")
            time.sleep(5)

    if not consumer:
        logger.error("Alert Worker failed to start: No Kafka connection.")
        return

    try:
        while True:
            # Poll frequently for fast response times
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error(f"Kafka worker error: {msg.error()}")
                continue

            try:
                # Decode and process the alert event
                data = json.loads(msg.value().decode('utf-8'))
                logger.debug(f"Handling alert event for {data.get('url')}")
                handle_alert_event(data)
            except Exception as e:
                logger.error(f"Failed to dispatch alert for monitor: {e}")

    finally:
        consumer.close()

if __name__ == "__main__":
    # Wait for cluster infrastructure to stabilize
    time.sleep(10)
    run_alert_worker()

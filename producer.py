import json
import time
import random
from confluent_kafka import Producer

# High-throughput configuration for Confluent Kafka
conf = {
    'bootstrap.servers': 'localhost:9092',
    'compression.type': 'snappy',
    'linger.ms': 20, 
    'batch.size': 65536
}
producer = Producer(conf)
topic = 'iot_truck_telemetry'

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")

def generate_telemetry():
    """Generates continuous mock truck data."""
    try:
        while True:
            payload = {
                "truck_id": f"TRK-{random.randint(1000, 9999)}",
                "temperature": round(random.uniform(-10.0, 50.0), 2),
                "timestamp": time.time()
            }
            producer.produce(
                topic,
                key=payload["truck_id"],
                value=json.dumps(payload).encode('utf-8'),
                callback=delivery_report
            )
            producer.poll(0)
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nShutting down producer...")
    finally:
        producer.flush()

if __name__ == '__main__':
    print(f"Starting high-throughput producer for {topic}...")
    generate_telemetry()
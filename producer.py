import json
import time
import random
from datetime import datetime
from confluent_kafka import Producer

conf = {'bootstrap.servers': 'localhost:9092'}
producer = Producer(conf)

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Delivered to {msg.topic()} -> {msg.value().decode('utf-8')}")

print("Starting Kafka Producer... Press Ctrl+C to stop.")

try:
    while True:
        data = {
            "truck_id": f"T-{random.randint(100, 105)}",
            "temp": round(random.uniform(-10.0, 80.0), 1),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        producer.produce('truck_telemetry', key=data['truck_id'], value=json.dumps(data), callback=delivery_report)
        producer.flush()
        time.sleep(1) 
except KeyboardInterrupt:
    print("Producer stopped.")
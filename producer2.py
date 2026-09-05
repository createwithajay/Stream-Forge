import json
import time
import random
from kafka import KafkaProducer

# Connect to the local Docker Kafka broker
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print("Blasting clean, error-free telemetry data... (Press Ctrl+C to stop)")

try:
    while True:
        # Strictly generating temperatures > 0 to avoid the filter and DLQ
        data = {
            "truck_id": f"TRUCK_{random.randint(100, 999)}",
            "temperature": round(random.uniform(20.0, 75.0), 2),
            "timestamp": time.time()
        }
        
        # Send to the exact topic your Faust worker is listening to
        producer.send('iot_truck_telemetry', value=data)
        print(f"Sent clean record: {data}")
        
        time.sleep(1)  # Send one record every second

except KeyboardInterrupt:
    print("\nProducer gracefully stopped.")
finally:
    producer.close()
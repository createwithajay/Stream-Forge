import json
import random
import time
from confluent_kafka import Producer

CONFIG = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'streamforge-iot-producer',
    'acks': 'all',                      # Ensures durability during worker failures
    'retries': 5,
    'retry.backoff.ms': 200,
    'queue.buffering.max.messages': 100000,
    'queue.buffering.max.kbytes': 102400,
    'batch.num.messages': 1000,
    'linger.ms': 10
}

producer = Producer(CONFIG)
TOPIC_NAME = "iot-truck-telemetry"
TOTAL_TRUCKS = 500  # Simulating fleet

def delivery_report(err, msg):
    if err is not None:
        print(f"[ERROR] Delivery failed: {err}")

def stream_telemetry():
    print(f"[START] Streaming IoT data to '{TOPIC_NAME}' with partition-key routing...")
    sent_count = 0
    start_time = time.time()
    
    try:
        while True:
            truck_num = random.randint(1, TOTAL_TRUCKS)
            truck_id = f"truck_{truck_num:04d}"
            payload = {
                "truck_id": truck_id,
                "temperature": round(random.uniform(-10.0, 95.0), 2),
                "timestamp": time.time()
            }
            
            # Keyed message ensures strict per-truck partition affinity
            producer.produce(
                topic=TOPIC_NAME,
                key=truck_id.encode('utf-8'),
                value=json.dumps(payload).encode('utf-8'),
                on_delivery=delivery_report
            )
            
            sent_count += 1
            if sent_count % 5000 == 0:
                producer.poll(0)
                elapsed = time.time() - start_time
                print(f"[STATUS] Sent: {sent_count:,} msgs | Throughput: {sent_count/elapsed:.2f} msg/sec")
            
            # High-throughput pacing (adjust or remove sleep for maximum stress)
            time.sleep(0.0001)

    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Flushing remaining messages...")
    finally:
        producer.flush(10)
        print("[FINISHED] Producer safely terminated.")

if __name__ == "__main__":
    stream_telemetry()
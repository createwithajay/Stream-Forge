import sys
import json
from confluent_kafka import Consumer, KafkaError

WORKER_NAME = sys.argv[1] if len(sys.argv) > 1 else "Worker-1"

conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'streamforge-workers',
    'auto.offset.reset': 'latest',
    'enable.auto.commit': True
}

consumer = Consumer(conf)

def print_assignment(consumer, partitions):
    assigned = [p.partition for p in partitions]
    print(f"\n[REBALANCE] {WORKER_NAME} ASSIGNED Partitions: {assigned}\n")

def print_revocation(consumer, partitions):
    revoked = [p.partition for p in partitions]
    print(f"\n[REBALANCE] {WORKER_NAME} REVOKED Partitions: {revoked}\n")

consumer.subscribe(
    ['iot-truck-telemetry'],
    on_assign=print_assignment,
    on_revoke=print_revocation
)

print(f"[{WORKER_NAME}] Started. Listening for messages...")

try:
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                print(f"[{WORKER_NAME}] Error: {msg.error()}")
                break

        data = json.loads(msg.value().decode('utf-8'))
        print(f"[{WORKER_NAME}] [Partition {msg.partition()}] {data['truck_id']}: {data['temperature']}°C")

except KeyboardInterrupt:
    print(f"\n[{WORKER_NAME}] Shutting down...")
finally:
    consumer.close()
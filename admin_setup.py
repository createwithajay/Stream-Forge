import sys
from confluent_kafka.admin import AdminClient, NewTopic

BOOTSTRAP_SERVERS = "localhost:9092"
TELEMETRY_TOPIC = "iot-truck-telemetry"
CHANGELOG_TOPIC = "streamforge-tumbling-window-changelog"
NUM_PARTITIONS = 8  # Allows distributing load across multiple workers
REPLICATION_FACTOR = 1

def configure_topics():
    admin = AdminClient({"bootstrap.servers": BOOTSTRAP_SERVERS})
    
    topics = [
        NewTopic(TELEMETRY_TOPIC, num_partitions=NUM_PARTITIONS, replication_factor=REPLICATION_FACTOR),
        NewTopic(CHANGELOG_TOPIC, num_partitions=NUM_PARTITIONS, replication_factor=REPLICATION_FACTOR)
    ]
    
    fs = admin.create_topics(topics)
    for topic, future in fs.items():
        try:
            future.result()
            print(f"[SUCCESS] Topic '{topic}' created with {NUM_PARTITIONS} partitions.")
        except Exception as e:
            print(f"[INFO] Topic '{topic}': {e}")

if __name__ == "__main__":
    configure_topics()
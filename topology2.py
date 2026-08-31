import json
import logging
import faust
import os

# ---------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("stream_forge.topology")

# Fetch port from environment or default to 6066 for clean execution
WORKER_PORT = int(os.getenv("FAUST_WEB_PORT", 6066))

# ---------------------------------------------------------
# App Initialization & Resilient Worker Settings
# ---------------------------------------------------------
app = faust.App(
    'stream-forge-topology',
    broker='kafka://localhost:9092',
    topic_partitions=3,
    store='memory://',  # Interfacing with local state / RocksDB
    consumer_auto_offset_reset='earliest',
    web_port=WORKER_PORT
)

# ---------------------------------------------------------
# Telemetry Record Schema
# ---------------------------------------------------------
class TruckTelemetry(faust.Record, serializer='json'):
    truck_id: str
    temperature: float
    timestamp: float

# Kafka Topics
raw_telemetry_topic = app.topic('iot_truck_telemetry', value_type=TruckTelemetry)
processed_topic = app.topic('truck_telemetry_processed', value_type=TruckTelemetry)
dlq_topic = app.topic('iot_telemetry_dlq', value_type=bytes)  # New Dead Letter Queue

# ---------------------------------------------------------
# Fault-Tolerant Processing DAG: Consume -> Filter -> Map
# ---------------------------------------------------------
@app.agent(raw_telemetry_topic)
async def process_telemetry_stream(stream):
    """
    Stream Processing Pipeline:
    1. Consume: Ingest real-time truck events.
    2. Filter: Discard corrupted/invalid readings (Temp <= 0).
    3. Map / Forward: Forward clean data downstream for aggregation.
    """
    async for event in stream:
        try:
            # Step 1: Validation / Filter Step
            if event.temperature <= 0:
                logger.warning(f"Filtered out invalid reading: Truck {event.truck_id} -> {event.temperature}°C")
                continue

            # Step 2: Transformation / Map Step
            transformed_event = TruckTelemetry(
                truck_id=str(event.truck_id).strip().upper(),
                temperature=round(float(event.temperature), 2),
                timestamp=event.timestamp
            )

            logger.info(f"Processed Event: {transformed_event.truck_id} | {transformed_event.temperature}°C")

            # Step 3: Forward downstream
            await processed_topic.send(value=transformed_event)

        except Exception as err:
            # Graceful failure: Route bad data to DLQ instead of crashing the partition
            logger.error(f"Poison pill detected! Routing to DLQ: {err}")
            await dlq_topic.send(value=str(event).encode('utf-8'))

# ---------------------------------------------------------
# Execution
# ---------------------------------------------------------
if __name__ == '__main__':
    app.main()
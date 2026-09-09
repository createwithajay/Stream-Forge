import json
import logging
import faust
import os


# Logging Configuration

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("stream_forge.topology")

# Fetch port from environment or default to 9090 for the Faust web server
WORKER_PORT = int(os.getenv("FAUST_WEB_PORT",9090))


# App Initialization & Resilient Worker Settings

app = faust.App(
    'stream-forge-topology',
    broker='kafka://localhost:9092',
    topic_partitions=3,
    store='memory://',
    consumer_auto_offset_reset='earliest',
    web_port=WORKER_PORT
)


# Telemetry Record Schema & Topics

class TruckTelemetry(faust.Record, serializer='json'):
    truck_id: str
    temperature: float
    timestamp: float

raw_telemetry_topic = app.topic('iot_truck_telemetry', value_type=TruckTelemetry)
processed_topic = app.topic('truck_telemetry_processed', value_type=TruckTelemetry)
dlq_topic = app.topic('iot_telemetry_dlq', value_type=bytes)


# Metrics Tracking

# Global counters exposed to Prometheus / Role 4
metrics = {
    "total_processed": 0,
    "invalid_filtered": 0,
    "dlq_errors": 0
}


# Fault-Tolerant Processing DAG: Consume -> Filter -> Map

@app.agent(raw_telemetry_topic)
async def process_telemetry_stream(stream):
    global metrics
    async for event in stream:
        try:
            # Step 1: Validation / Filter Step
            if event.temperature <= 0:
                metrics["invalid_filtered"] += 1
                logger.warning(f"Filtered out invalid reading: Truck {event.truck_id} -> {event.temperature}°C")
                continue

            # Step 2: Transformation / Map Step
            transformed_event = TruckTelemetry(
                truck_id=str(event.truck_id).strip().upper(),
                temperature=round(float(event.temperature), 2),
                timestamp=event.timestamp
            )

            metrics["total_processed"] += 1
            logger.info(f"Processed Event: {transformed_event.truck_id} | {transformed_event.temperature}°C")

            # Step 3: Forward downstream
            await processed_topic.send(value=transformed_event)

        except Exception as err:
            # Route bad data to DLQ and increment error metric
            metrics["dlq_errors"] += 1
            logger.error(f"Poison pill detected! Routing to DLQ: {err}")
            await dlq_topic.send(value=str(event).encode('utf-8'))


# Web Endpoints (Metrics & Health)

@app.page('/health')
class HealthCheck(faust.web.View):
    """Provides a live status ping for the dashboard."""
    async def get(self, request, **kwargs):
        return self.json({"status": "healthy", "service": "stream-forge-topology", "port": WORKER_PORT})

@app.page('/status/data')
class MetricsView(faust.web.View):
    """Exposes processing counters for Role 4's Prometheus scraper."""
    async def get(self, request, **kwargs):
        return self.json(metrics)


# Execution

if __name__ == '__main__':
    app.main()
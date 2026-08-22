import json
import bytewax.operators as op
from bytewax.dataflow import Dataflow
from bytewax.connectors.kafka import KafkaSource

flow = Dataflow("stream_forge_topology")

stream = op.input(
    "kafka_in", 
    flow, 
    KafkaSource(brokers=["localhost:9092"], topics=["truck_telemetry"])
)

def parse_payload(msg):
    key_bytes, value_bytes = msg
    if value_bytes is None:
        return None
    return json.loads(value_bytes.decode('utf-8'))

parsed_stream = op.filter_map("parse_json", stream, parse_payload)

# Day 3: Filter out faulty sensor data (keep only realistic temps between -20 and 60 Celsius)
def filter_extreme_temps(data):
    return -20.0 <= data["temp"] <= 60.0

clean_stream = op.filter("filter_temps", parsed_stream, filter_extreme_temps)

# Verify the final cleaned data
op.inspect("print_clean_data", clean_stream)

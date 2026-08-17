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

# Day 2: Safely decode the Kafka byte payload into a Python dictionary
def parse_payload(msg):
    key_bytes, value_bytes = msg
    if value_bytes is None:
        return None
    return json.loads(value_bytes.decode('utf-8'))

# filter_map will process the data and drop any empty/invalid messages
parsed_stream = op.filter_map("parse_json", stream, parse_payload)

op.inspect("print_parsed", parsed_stream)

import bytewax.operators as op
from bytewax.dataflow import Dataflow
from bytewax.connectors.kafka import KafkaSource

# Initialize the core dataflow pipeline
flow = Dataflow("stream_forge_topology")

# Day 1: Connect directly to the local Kafka broker Role 1 set up
stream = op.input(
    "kafka_in", 
    flow, 
    KafkaSource(brokers=["localhost:9092"], topics=["truck_telemetry"])
)

# Print the raw bytes coming from Kafka
op.inspect("print_raw", stream)

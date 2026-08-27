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

# FIXED: Extract data using the object's .value attribute
def parse_payload(msg):
    if msg.value is None:
        return None
    return json.loads(msg.value.decode('utf-8'))

parsed_stream = op.filter_map("parse_json", stream, parse_payload)

def filter_extreme_temps(data):
    return -20.0 <= data["temp"] <= 60.0

clean_stream = op.filter("filter_temps", parsed_stream, filter_extreme_temps)

# Week 3, Day 1: Key the data by truck_id
def extract_truck_id(data):
    return (data["truck_id"], data)

keyed_stream = op.map("key_on_truck", clean_stream, extract_truck_id)

# Week 3, Day 2: Stateful Aggregation (Running Average)
def calculate_running_average(state, data):
    if state is None:
        count = 0
        total_temp = 0.0
    else:
        count, total_temp = state
    
    count += 1
    total_temp += data["temp"]
    
    avg_temp = round(total_temp / count, 2)
    
    new_state = (count, total_temp)
    output = {"truck_id": data["truck_id"], "running_avg_temp": avg_temp}
    
    return new_state, output

avg_stream = op.stateful_map("truck_avg", keyed_stream, calculate_running_average)

op.inspect("print_avg", avg_stream)

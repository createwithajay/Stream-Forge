import bytewax.operators as op
from bytewax.dataflow import Dataflow
from bytewax.testing import TestingSource
from data_source import mock_telemetry

# Initialize the core dataflow pipeline
flow = Dataflow("stream_forge_topology")

# Connect the mock telemetry source to the stream
stream = op.input("mock_input", flow, TestingSource(mock_telemetry))

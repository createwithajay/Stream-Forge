#!/bin/bash
# Stream Forge - Topology Worker Execution Script

echo "Starting Faust Stream Topology Worker..."
source venv/bin/activate
export FAUST_WEB_PORT=${1:-6066}
echo "Booting Faust on port $FAUST_WEB_PORT..."
python topology2.py worker -l info
#!/bin/bash
# Stream-Forge Faust Topology Boot Script
export FAUST_WEB_PORT=${1:-9090}
echo "Starting Faust Stream Topology Worker on port $FAUST_WEB_PORT..."
faust -A topology2 worker -l info
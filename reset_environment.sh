#!/bin/bash

# Stop any running servers
echo "Stopping running servers..."
./stop_react_servers.sh 2>/dev/null

# Kill any remaining processes
echo "Killing any remaining processes..."
pkill -f "node|uvicorn" 2>/dev/null

# Clean up logs
echo "Cleaning up logs..."
mkdir -p logs
rm -f logs/*.log

# Remove any PID files
echo "Removing PID files..."
rm -f logs/*.txt

echo "Environment reset complete. You can now run './run_react_servers.sh' to start fresh." 
#!/bin/bash

# Create logs directory if it doesn't exist
if [ ! -f logs/server_pids.txt ]; then
  echo "No server PIDs found. Servers might not be running."
  exit 0
fi

# Read PIDs from file
read API_PID WEB_PID < logs/server_pids.txt

# Stop web server
if kill -0 $WEB_PID 2>/dev/null; then
  echo "Stopping web server (PID: $WEB_PID)..."
  kill $WEB_PID
  sleep 1
  if kill -0 $WEB_PID 2>/dev/null; then
    echo "Web server still running, force stopping..."
    kill -9 $WEB_PID
  fi
else
  echo "Web server (PID: $WEB_PID) is not running."
fi

# Stop API server
if kill -0 $API_PID 2>/dev/null; then
  echo "Stopping API server (PID: $API_PID)..."
  kill $API_PID
  sleep 1
  if kill -0 $API_PID 2>/dev/null; then
    echo "API server still running, force stopping..."
    kill -9 $API_PID
  fi
else
  echo "API server (PID: $API_PID) is not running."
fi

echo "All servers stopped."
rm logs/server_pids.txt 
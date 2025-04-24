#!/bin/bash

# Load the PIDs from the file
if [ -f logs/react_server_pids.txt ]; then
  read API_PID FRONTEND_PID < logs/react_server_pids.txt
  
  # Stop the frontend process
  if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "Stopping React frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID
    echo "React frontend stopped."
  else
    echo "React frontend is not running."
  fi
  
  # Stop the API process
  if [ ! -z "$API_PID" ] && kill -0 $API_PID 2>/dev/null; then
    echo "Stopping FastAPI server (PID: $API_PID)..."
    kill $API_PID
    echo "FastAPI server stopped."
  else
    echo "FastAPI server is not running."
  fi
  
  # Remove the PID file
  rm logs/react_server_pids.txt
else
  echo "No running servers found. (logs/react_server_pids.txt not found)"
fi

echo "All servers stopped." 
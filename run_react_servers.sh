#!/bin/bash

# Set default port values
API_PORT=8000
WEB_PORT=3000

# Allow overriding the port values
while getopts "a:w:" opt; do
  case $opt in
    a) API_PORT=$OPTARG ;;
    w) WEB_PORT=$OPTARG ;;
    *) echo "Usage: $0 [-a API_PORT] [-w WEB_PORT]" >&2; exit 1 ;;
  esac
done

# Create logs directory if it doesn't exist
mkdir -p logs

echo "Starting FastAPI server on port $API_PORT..."
cd $(dirname $0)
export PORT=$API_PORT
cd api && python3 -m uvicorn main:app --port $API_PORT > ../logs/api_server.log 2>&1 &
API_PID=$!
cd ..

# Wait a moment to let API server start
sleep 2

# Check if API server is running
if ! kill -0 $API_PID 2>/dev/null; then
  echo "Error: FastAPI server failed to start. Check logs/api_server.log for details."
  exit 1
fi

echo "Starting React frontend on port $WEB_PORT..."
cd pepperpy-ui
export PORT=$WEB_PORT
export VITE_API_URL="http://localhost:$API_PORT"
npm run dev > ../logs/react_frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait a moment to let frontend start
sleep 5

# Check if frontend is running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
  echo "Error: React frontend failed to start. Check logs/react_frontend.log for details."
  kill $API_PID
  exit 1
fi

echo "Both servers are running:"
echo "- FastAPI server: http://localhost:$API_PORT (PID: $API_PID)"
echo "- React frontend: http://localhost:$WEB_PORT (PID: $FRONTEND_PID)"
echo
echo "To access the application, open http://localhost:$WEB_PORT in your browser"
echo "View logs at:"
echo "- logs/api_server.log"
echo "- logs/react_frontend.log"

# Save PIDs for later use
echo "$API_PID $FRONTEND_PID" > logs/react_server_pids.txt 
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
python -m api.main > logs/api_server.log 2>&1 &
API_PID=$!

# Wait a moment to let API server start
sleep 2

# Check if API server is running
if ! kill -0 $API_PID 2>/dev/null; then
  echo "Error: FastAPI server failed to start. Check logs/api_server.log for details."
  exit 1
fi

echo "Starting Express web server on port $WEB_PORT..."
cd playground_web
export PORT=$WEB_PORT
export API_URL="http://localhost:$API_PORT"
node server.js > ../logs/web_server.log 2>&1 &
WEB_PID=$!

# Wait a moment to let web server start
sleep 2

# Check if web server is running
if ! kill -0 $WEB_PID 2>/dev/null; then
  echo "Error: Express web server failed to start. Check logs/web_server.log for details."
  kill $API_PID
  exit 1
fi

echo "Both servers are running:"
echo "- FastAPI server: http://localhost:$API_PORT (PID: $API_PID)"
echo "- Web server: http://localhost:$WEB_PORT (PID: $WEB_PID)"
echo
echo "To access the application, open http://localhost:$WEB_PORT in your browser"
echo "To stop the servers, run: kill $API_PID $WEB_PID"
echo "View logs at logs/api_server.log and logs/web_server.log"

# Save PIDs for later use
echo "$API_PID $WEB_PID" > logs/server_pids.txt 
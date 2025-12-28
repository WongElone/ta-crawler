#!/bin/sh

# Get the PID from the argument
PYTHON_PID=$1

if [ -z "$PYTHON_PID" ]; then
  echo "No PID provided."
  exit 1
fi

echo "Shutting down crawler PID: $PYTHON_PID"

# Send SIGTERM to the process for graceful shutdown
kill -TERM $PYTHON_PID

# Wait for the process to exit (with a timeout, e.g., 30 seconds)
timeout=30
count=0
while ps -p $PYTHON_PID > /dev/null; do
  if [ $count -ge $timeout ]; then
    echo "Timeout reached, sending SIGKILL."
    kill -KILL $PYTHON_PID
    exit 1
  fi
  echo "Waiting for crawler PID: $PYTHON_PID to exit..."
  sleep 1
  count=$((count + 1))
done

echo "crawler PID: $PYTHON_PID stopped gracefully."
exit 0
#!/bin/sh
set -e

CRAWLER_LOG_DIR=/var/log/app
mkdir -p $CRAWLER_LOG_DIR

# Trap SIGTERM and call the shutdown script with PID
trap 'echo "Received SIGTERM, shutting down gracefully..."; ./stop.sh $PYTHON_PID' TERM INT

echo "CRAWLER_MODE is set to: $CRAWLER_MODE"

if [ "$CRAWLER_MODE" = "test" ]; then
  echo "RUNNING Tests"
  uv run python -m crawler.test 2>> $CRAWLER_LOG_DIR/crawler.stderr.log & PYTHON_PID=$!
elif [ "$CRAWLER_MODE" = "run" ]; then
  echo "Starting Crawler"
  uv run python -m crawler.main 2>> $CRAWLER_LOG_DIR/crawler.stderr.log & PYTHON_PID=$!
else
  echo "Check config"
  uv run python -m crawler.check_config 2>> $CRAWLER_LOG_DIR/crawler.stderr.log & PYTHON_PID=$!
fi

# Wait for the Python process to exit (keeps the container running)
wait $PYTHON_PID

echo "crawler stopped successfully"

# Optional: Exit with the Python process's exit code
exit $?
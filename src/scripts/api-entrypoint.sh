#!/bin/sh

# Exit on error
set -e

# This script is called by wait-for-services.sh after dependent services are ready.

# Initialize the database if RUN_INIT_DB is true
if [ "$RUN_INIT_DB" = "true" ]; then
  echo "RUN_INIT_DB is true. Initializing database..."
  poetry run python -m trendscout.db.init_db
else
  echo "RUN_INIT_DB is not 'true' or not set. Skipping database initialization."
fi

# Start the Uvicorn server
echo "Starting Uvicorn server..."
# Using --reload for development.
# --log-level debug matches original Dockerfile CMD.
exec poetry run uvicorn trendscout.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

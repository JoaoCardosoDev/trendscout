#!/bin/bash

wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    
    echo "Waiting for $service to be ready..."
    while ! nc -z $host $port; do
        echo "$service is not ready yet..."
        sleep 1
    done
    echo "$service is ready!"
}

# Wait for PostgreSQL
wait_for_service ${POSTGRES_SERVER} ${POSTGRES_PORT} "PostgreSQL"

# Wait for Redis
wait_for_service ${REDIS_HOST} ${REDIS_PORT} "Redis"

# Wait for Ollama
wait_for_service "ollama" "11434" "Ollama"

echo "All services are ready. Starting the application..."

# Start the application
exec "$@"

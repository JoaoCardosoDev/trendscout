#!/bin/bash

# Maximum number of retries
MAX_RETRIES=30
# Delay between retries in seconds
RETRY_DELAY=2

wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local retries=0
    
    echo "Waiting for $service to be ready..."
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if nc -z $host $port; then
            echo "$service is ready!"
            return 0
        fi
        
        retries=$((retries + 1))
        remaining=$((MAX_RETRIES - retries))
        echo "$service is not ready yet... ($remaining attempts remaining)"
        sleep $RETRY_DELAY
    done
    
    echo "Error: $service did not become ready in time"
    return 1
}

echo "Starting service checks..."

# Wait for PostgreSQL
if ! wait_for_service ${POSTGRES_SERVER} ${POSTGRES_PORT} "PostgreSQL"; then
    echo "Error: PostgreSQL is not available"
    exit 1
fi

# Wait for Redis
if ! wait_for_service ${REDIS_HOST} ${REDIS_PORT} "Redis"; then
    echo "Error: Redis is not available"
    exit 1
fi

# Wait for Ollama
if ! wait_for_service "ollama" "11434" "Ollama"; then
    echo "Error: Ollama is not available"
    exit 1
fi

echo "All services are ready. Starting the application..."

# Start the application with exec to properly handle signals
exec "$@"

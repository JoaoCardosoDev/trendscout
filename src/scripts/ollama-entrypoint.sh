#!/bin/sh
set -e

echo "Starting Ollama service entrypoint script..."

# Start ollama serve in the background
ollama serve &
OLLAMA_PID=$!
echo "Ollama server process started in background with PID $OLLAMA_PID."

# Wait for the server to initialize
echo "Waiting 15 seconds for Ollama server to initialize..."
sleep 15

# Attempt to pull the llama2 model
echo "Attempting to pull llama2 model..."
if ollama pull llama2; then
  echo "llama2 model pulled successfully."
else
  echo "Failed to pull llama2 model. The server will continue running without it being pre-pulled by this script."
  echo "You might need to pull it manually later or check Ollama server logs for more details."
fi

echo "Ollama setup complete. Keeping Ollama server (PID $OLLAMA_PID) running..."
# Wait for the ollama serve process. If it exits, this script (and the container) will exit.
wait $OLLAMA_PID

echo "Ollama server process (PID $OLLAMA_PID) has exited."
exit 0

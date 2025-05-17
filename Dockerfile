FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock* ./
COPY src/ ./src/
COPY tests/ ./tests/

# Make wait-for-services script executable
RUN chmod +x /app/src/scripts/wait-for-services.sh

# Configure Poetry
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-root

# Run the application with wait-for-services script
CMD ["/app/src/scripts/wait-for-services.sh", "poetry", "run", "uvicorn", "src.trendscout.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]

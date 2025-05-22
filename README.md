# Trendscout

## Overview

Trendscout is a backend solution designed for trend analysis, content generation, and scheduling, leveraging AI agents powered by Crew AI and local LLMs via Ollama. It provides a robust system for developers and organizations seeking to automate these processes, offering actionable insights through a clean API interface and a simple web UI.

The project aims to deliver a scalable Python backend built with FastAPI, utilizing PostgreSQL for data storage and Redis for asynchronous task queuing.

## Key Features

*   **AI-Powered Agents**:
    *   **Trend Analyzer**: Identifies trending topics.
    *   **Content Generator**: Creates post ideas based on identified trends.
    *   **Scheduler**: Determines optimal publishing times for content.
*   **Crew AI Workflow**: Implements a "Trend-to-Post" crew that orchestrates the Trend Analyzer, Content Generator, and Scheduler agents in a chained workflow to provide a complete solution from trend identification to a scheduled content idea.
*   **Asynchronous Task Processing**: Utilizes a Redis-based queue and a dedicated worker service to handle long-running agent and crew tasks efficiently.
*   **RESTful API**: Clean and well-documented API built with FastAPI for interaction with agents and managing tasks.
*   **Simple Web UI**: A basic user interface served at `/ui` for easy login, task creation (for both single agents and the full crew workflow), and real-time status tracking, including intermediate steps for crew tasks.
*   **Database Storage**: PostgreSQL stores user information and task details, including inputs, results, and intermediate steps from crew workflows.
*   **Dockerized Environment**: Fully containerized setup using Docker and Docker Compose for easy deployment and consistent environments across all services (API, worker, PostgreSQL, Redis, Ollama).
*   **Local LLM Integration**: Uses Ollama to serve local language models (e.g., Llama 3), providing flexibility and control over AI capabilities.
*   **Authentication**: Secure JWT-based authentication for API endpoints.
*   **Structured Logging**: Comprehensive logging for monitoring and debugging.

## Technologies Used

*   **Backend Framework**: FastAPI
*   **Programming Language**: Python
*   **AI Orchestration**: Crew AI
*   **Local LLM Serving**: Ollama
*   **Database**: PostgreSQL
*   **ORM**: SQLAlchemy
*   **Task Queue**: Redis
*   **Authentication**: JWT
*   **Containerization**: Docker, Docker Compose
*   **Dependency Management**: Poetry
*   **Testing**: pytest

## Prerequisites

*   **Docker:** To build and run the containerized application.
*   **Docker Compose:** To manage multi-container Docker applications.
*   **Git:** To clone the repository.
*   **(Optional) Make:** The project includes a `Makefile` for convenience commands.

## Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/JoaoCardosoDev/trendscout
    cd trendscout
    ```

2.  **Environment Variables:**
    The application uses a `.env` file for configuration. The project includes a pre-configured `.env` file suitable for the Docker Compose setup. You can review it and modify if necessary (e.g., `OLLAMA_MODEL_NAME`, `FIRST_SUPERUSER_EMAIL`, `FIRST_SUPERUSER_PASSWORD`).

3.  **Building and Running the Application:**
    Use the provided `Makefile` for convenience:
    ```bash
    make docker-up
    ```
    This command will build Docker images and start all services (API, worker, PostgreSQL, Redis, Ollama) in detached mode. The Ollama service will attempt to pull the specified model (default: `llama3:latest`) if not already present.

    Alternatively, use Docker Compose directly:
    ```bash
    docker-compose up -d --build
    ```

    **Important Note on Chained Prompts:**
    The "Full Trend-to-Post Workflow (Crew)" involves multiple AI agents working in sequence. **Depending on your machine's performance and the complexity of the topic, this chained prompt can take up to 15 minutes or more to complete.** Please be patient when running these tasks.

4.  **Verifying Services:**
    Check service status:
    ```bash
    docker-compose ps
    ```
    View logs:
    ```bash
    docker-compose logs api
    docker-compose logs worker
    docker-compose logs ollama
    ```
    The API will be accessible at `http://localhost:8000`.

## Usage

### API Usage
The API is documented using Swagger UI and ReDoc:
*   **Swagger UI:** `http://localhost:8000/docs`
*   **ReDoc:** `http://localhost:8000/redoc`

Refer to the `USER_GUIDE.md` for detailed API endpoint examples.

### Simple UI Usage
A basic web UI is available for interacting with the system:
*   Navigate to `http://localhost:8000/ui` in your browser.
*   Log in using the credentials (e.g., `FIRST_SUPERUSER_EMAIL` and `FIRST_SUPERUSER_PASSWORD` from your `.env` file).
*   Create tasks for individual agents or the full "Trend-to-Post" crew.
*   Monitor task status, view results, and see intermediate steps for crew workflows.

Refer to the `USER_GUIDE.md` for more detailed UI instructions.

## Running Tests

To run the test suite (uses `pytest`):
*   Using Make:
    ```bash
    make test
    ```
*   Using Docker Compose:
    ```bash
    docker-compose exec api pytest /app/tests
    ```

## Project Structure

*   `src/trendscout/`: Main application code.
    *   `agents/`: Definitions for AI agents and crews.
    *   `api/`: FastAPI endpoints and schemas.
    *   `core/`: Core application logic (config, security, logging, etc.).
    *   `db/`: Database models, session management, initialization.
    *   `models/`: Pydantic models and SQLAlchemy ORM models.
    *   `static/`: HTML, CSS, JS for the simple UI.
    *   `main.py`: FastAPI application entry point.
    *   `worker.py`: Background worker for processing tasks from the queue.
*   `tests/`: Pytest test suite.
*   `scripts/`: Shell scripts for Docker entrypoints and service management.
*   `Dockerfile`: Defines the Docker image for the application.
*   `docker-compose.yml`: Defines all services for the application stack.
*   `Makefile`: Convenience commands for development and operations.
*   `pyproject.toml`: Project metadata and dependencies (Poetry).
*   `USER_GUIDE.md`: Detailed guide for users.
*   `PROJECT_REPORT.md`: Summary report of the project.

## Stopping the Application

*   Using Make:
    ```bash
    make docker-down
    ```
*   Using Docker Compose:
    ```bash
    docker-compose down
    ```

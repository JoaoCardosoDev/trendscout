# Trendscout User Guide

## Table of Contents
- [Trendscout User Guide](#trendscout-user-guide)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Prerequisites](#prerequisites)
  - [Installation \& Setup](#installation--setup)
    - [Cloning the Repository](#cloning-the-repository)
    - [Environment Variables](#environment-variables)
    - [Building and Running the Application](#building-and-running-the-application)
    - [Verifying Services](#verifying-services)
  - [Usage](#usage)
    - [API Usage](#api-usage)
    - [Simple UI Usage](#simple-ui-usage)
  - [Running Tests](#running-tests)
  - [Troubleshooting](#troubleshooting)

## Introduction
Trendscout is a Python backend solution designed to integrate advanced AI agent capabilities using Crew AI. It enables efficient handling of complex tasks such as trend analysis, content generation, and scheduling by delegating responsibilities to AI agents. The system is built with FastAPI, uses PostgreSQL for data storage, Redis for task queuing, and Ollama for local AI model serving.

## Prerequisites
Before you begin, ensure you have the following installed on your system:
*   **Docker:** To build and run the containerized application. Get Docker from [docker.com](https://www.docker.com/get-started).
*   **Docker Compose:** To manage multi-container Docker applications. It's usually included with Docker Desktop.
*   **Git:** To clone the repository.
*   **(Optional) Make:** The project includes a `Makefile` for convenience commands. If you don't have `make`, you can run the Docker Compose commands directly.

## Installation & Setup

### Cloning the Repository
First, clone the Trendscout repository to your local machine:
```bash
git clone https://github.com/JoaoCardosoDev/trendscout
cd trendscout
```


### Environment Variables
The application uses environment variables for configuration. These are typically managed in a `.env` file.
1.  Copy the example environment file (if one is provided, e.g., `.env.example`) to `.env`:
    ```bash
    cp .env.example .env
    ```
    If no `.env.example` exists, create a `.env` file in the root of the project.
2.  Review and update the variables in the `.env` file as needed. Key variables include:
    *   `POSTGRES_SERVER`
    *   `POSTGRES_USER`
    *   `POSTGRES_PASSWORD`
    *   `POSTGRES_DB`
    *   `REDIS_HOST`
    *   `OLLAMA_API_BASE_URL` (usually `http://ollama:11434/api` when running in Docker)
    *   `OLLAMA_MODEL_NAME` (e.g., `llama3:latest`)
    *   `SECRET_KEY` (for JWT token generation)
    *   `ALGORITHM` (e.g., `HS256`)
    *   `ACCESS_TOKEN_EXPIRE_MINUTES`
    *   `FIRST_SUPERUSER_EMAIL`
    *   `FIRST_SUPERUSER_PASSWORD`

    **Note:** The `.env` file provided in the project is already configured for the Docker Compose setup (e.g., service names like `postgres`, `redis`, `ollama` are used as hostnames).

### Building and Running the Application
The project uses Docker Compose to manage all its services (API, worker, database, Redis, Ollama).

You can use the provided `Makefile` for convenience:
*   To build the Docker images and start all services:
    ```bash
    make docker-up
    ```
*   Alternatively, you can use Docker Compose commands directly:
    ```bash
    docker-compose up -d --build
    ```
    The `-d` flag runs the containers in detached mode (in the background). The `--build` flag ensures images are rebuilt if there are changes.

This command will:
1.  Build the Docker image for the Trendscout application (API and worker).
2.  Pull official images for PostgreSQL, Redis, and Ollama.
3.  Start all services as defined in `docker-compose.yml`.
4.  The `wait-for-services.sh` script will ensure dependent services (Postgres, Redis, Ollama) are ready before the API and worker start.
5.  The Ollama entrypoint script (`ollama-entrypoint.sh`) will attempt to pull the model specified by `OLLAMA_MODEL_NAME` if it's not already available locally within the Ollama container.
6.  The API entrypoint script (`api-entrypoint.sh`) will run database migrations (Alembic) and initialize the database with a superuser if it's the first run.

### Verifying Services
Once the `docker-compose up` command completes, you can check the status of the services:
```bash
docker-compose ps
```
You should see services like `api`, `worker`, `postgres`, `redis`, and `ollama` running.

You can also check the logs for each service:
```bash
docker-compose logs api
docker-compose logs worker
docker-compose logs ollama
# etc.
```
The API should be accessible at `http://localhost:8000` by default (or the port configured in `docker-compose.yml`).

## Usage

### API Usage
Trendscout exposes its functionalities via a RESTful API built with FastAPI.

**API Documentation:**
FastAPI automatically generates interactive API documentation:
*   **Swagger UI:** Accessible at `http://localhost:8000/docs`
*   **ReDoc:** Accessible at `http://localhost:8000/redoc`

These interfaces allow you to explore all available endpoints, view their request/response schemas, and even try them out directly from your browser.

**Key API Endpoints:**
*   **Authentication:**
    *   `POST /api/v1/auth/login`: Authenticate to get an access token. Requires `username` (email) and `password` in a form data payload.
*   **Users:**
    *   `POST /api/v1/users/`: Create a new user (superuser only).
    *   `GET /api/v1/users/me`: Get current user details.
*   **Tasks:**
    *   `POST /api/v1/tasks/`: Create a new agent task.
        *   Payload example for a single agent:
            ```json
            {
              "agent_type": "trend_analyzer",
              "input_data": { "query": "latest AI trends" }
            }
            ```
        *   Payload example for the "Trend-to-Post" crew:
            ```json
            {
              "agent_type": "trend_to_post_crew",
              "input_data": { "topic": "sustainable energy" }
            }
            ```
    *   `GET /api/v1/tasks/{task_id}`: Get the status and result of a specific task.
    *   `GET /api/v1/tasks/`: List all tasks for the current user.
*   **Health Check:**
    *   `GET /api/v1/health/`: Check the health of the API service.

**Example API Interaction (using cURL):**
1.  **Login:**
    ```bash
    curl -X POST -F "username=your_superuser_email@example.com" -F "password=your_superuser_password" http://localhost:8000/api/v1/auth/login
    ```
    This will return an access token. Let's say it's `YOUR_ACCESS_TOKEN`.

2.  **Create a Task:**
    ```bash
    curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
    -d '{
      "agent_type": "trend_analyzer",
      "input_data": { "query": "future of remote work" }
    }' \
    http://localhost:8000/api/v1/tasks/
    ```
    This will return the created task details, including its `task_id`.

3.  **Check Task Status:**
    ```bash
    curl -X GET -H "Authorization: Bearer YOUR_ACCESS_TOKEN" http://localhost:8000/api/v1/tasks/{task_id_from_previous_step}
    ```

### Simple UI Usage
A basic web UI is provided for interacting with the Trendscout system.

**Accessing the UI:**
Navigate to `http://localhost:8000/ui` in your web browser.

**Features:**
1.  **Login:**
    *   Enter the email and password for a registered user (e.g., the `FIRST_SUPERUSER_EMAIL` and `FIRST_SUPERUSER_PASSWORD` defined in your `.env` file).
    *   Click "Login".
2.  **Task Creation:**
    *   Once logged in, you'll see the task creation form.
    *   **Select Task Type:** Choose from available agents/crews (e.g., "Trend Analyzer", "Content Generator", "Scheduler", "Full Trend-to-Post Workflow").
    *   **Enter Input:** Provide the required input for the selected task type (e.g., a query for Trend Analyzer, a topic for the Trend-to-Post crew).
    *   Click "Create Task".
3.  **Task Status Display:**
    *   Newly created tasks will appear in the "Task Status" area.
    *   The UI polls the backend every 5 seconds to update task statuses.
    *   For each task, you'll see:
        *   Task ID, Agent Type, Status, Creation Time.
        *   Input Data (pretty-printed).
        *   Result (pretty-printed once completed).
        *   Error (if any).
        *   Intermediate Steps (for crew tasks, showing output from each agent in the workflow, pretty-printed).
4.  **Logout:**
    *   A "Logout" button is available to clear your session.

## Running Tests
The project includes a suite of tests written with `pytest`.

To run the tests:
*   If you have `make` installed:
    ```bash
    make test
    ```
*   Alternatively, using Docker Compose directly:
    ```bash
    docker-compose exec api pytest /app/tests
    ```
    Or, if you want to run tests with coverage:
    ```bash
    docker-compose exec api pytest --cov=/app/src/trendscout /app/tests
    ```
This command executes the tests within the `api` service container, ensuring they run in the same environment as the application.

## Troubleshooting
*   **Service Connection Issues:**
    *   Ensure Docker and Docker Compose are running correctly.
    *   Check service logs (`docker-compose logs <service_name>`) for specific errors.
    *   Verify that hostnames in `.env` (e.g., `POSTGRES_SERVER=postgres`, `REDIS_HOST=redis`) match the service names in `docker-compose.yml`.
*   **Ollama Model Not Found:**
    *   The `ollama-entrypoint.sh` script attempts to pull the model specified by `OLLAMA_MODEL_NAME`. If this fails (e.g., due to network issues or incorrect model name), agent tasks will fail.
    *   Check `docker-compose logs ollama`. You can manually pull a model into the running Ollama container:
        ```bash
        docker-compose exec ollama ollama pull <model_name>
        ```
        (e.g., `docker-compose exec ollama ollama pull llama3:latest`)
*   **Database Migration Issues:**
    *   Migrations are run automatically by `api-entrypoint.sh`. If there are issues, check `docker-compose logs api`.
    *   You can manually run migrations:
        ```bash
        docker-compose exec api alembic upgrade head
        ```
*   **"No tasks created or being tracked yet." in UI:**
    *   This is normal if you haven't created any tasks after logging in. Create a task using the form.
*   **Task stuck in "pending" or "processing":**
    *   Check `docker-compose logs worker` for errors. The worker service is responsible for processing tasks.
    *   Check `docker-compose logs ollama` if the task involves AI model interaction.
    *   Ensure Redis is running (`docker-compose logs redis`).

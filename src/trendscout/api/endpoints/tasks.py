from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any
import uuid

from ...core.queue import queue_manager
from ...db.session import get_db
from .. import schemas
from ...models.task import AgentTask
from ...models.user import User
from .auth import get_current_user

router = APIRouter(tags=["tasks"])


@router.post(
    "/tasks/",
    response_model=schemas.TaskInDB,
    summary="Create new agent task",
    description="""
    Create a new task to be executed by an AI agent.

    Available agent types:
    * `trend_analyzer`: Analyzes social media platforms to identify trending topics.
      Input: `{"query": "your topic for trend analysis"}`
      Example:
      ```json
      {
        "agent_type": "trend_analyzer",
        "input_data": { "query": "AI in education" }
      }
      ```

    * `content_generator`: Creates engaging post ideas based on trends or a topic.
      Input: `{"query": "your topic or trend summary for content generation"}`
      Example:
      ```json
      {
        "agent_type": "content_generator",
        "input_data": { "query": "Post ideas for AI in education trends" }
      }
      ```

    * `scheduler`: Determines optimal publishing times for given content characteristics.
      Input: `{"query": "details about content and audience for scheduling"}`
      Example:
      ```json
      {
        "agent_type": "scheduler",
        "input_data": { "query": "Schedule blog post about AI for tech professionals" }
      }
      ```

    * `trend_to_post_crew`: A full workflow that takes a topic, analyzes trends, generates content, and suggests a schedule.
      Input: `{"topic": "your initial topic"}`
      Example:
      ```json
      {
        "agent_type": "trend_to_post_crew",
        "input_data": { "topic": "sustainable fashion" }
      }
      ```

    Tasks are processed asynchronously. Use the returned task_id to check the status and retrieve results.
    """,
    responses={
        201: {
            "description": "Task created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "task_id": "550e8400-e29b-41d4-a716-446655440000",
                        "agent_type": "trend_analyzer",
                        "status": "pending",
                        "input_data": {
                            "platforms": ["twitter", "reddit"],
                            "categories": ["technology"],
                            "time_range": "24h",
                        },
                        "user_id": 1,
                        "created_at": "2025-05-10T21:45:00",
                        "updated_at": None,
                        "completed_at": None,
                        "execution_time": None,
                        "result": None,
                        "error": None,
                    }
                }
            },
        }
    },
)
async def create_task(
    *,
    db: Session = Depends(get_db),
    task_in: schemas.TaskCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create new agent task."""
    # Create task in database
    task_id = str(uuid.uuid4())
    db_task = AgentTask(
        task_id=task_id,
        agent_type=task_in.agent_type,
        status="pending",
        input_data=task_in.input_data,
        user_id=current_user.id,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # Add task to queue
    queue_manager.enqueue_task(
        task_in.agent_type,
        {
            "task_id": task_id,
            "agent_type": task_in.agent_type,
            "input_data": task_in.input_data,
            "user_id": current_user.id,
        },
    )

    return db_task


@router.get(
    "/tasks/{task_id}",
    response_model=schemas.TaskInDB,
    summary="Get task by ID",
    description="""
    Retrieve a specific task by its UUID.

    The task status can be one of:
    * `pending`: Task is waiting to be processed
    * `running`: Task is currently being processed
    * `completed`: Task has finished successfully
    * `failed`: Task encountered an error

    When the task is completed, the result field will contain the agent's output:
    ```json
    {
      "status": "completed",
      "result": {
        "trends": [
          {
            "topic": "AI in Healthcare",
            "score": 0.85,
            "sources": ["twitter", "reddit"],
            "sentiment": "positive"
          }
        ],
        "analysis": "Healthcare AI is trending due to..."
      }
    }
    ```
    """,
    responses={
        200: {
            "description": "Task information",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "task_id": "550e8400-e29b-41d4-a716-446655440000",
                        "agent_type": "trend_analyzer",
                        "status": "completed",
                        "input_data": {
                            "platforms": ["twitter", "reddit"],
                            "categories": ["technology"],
                            "time_range": "24h",
                        },
                        "user_id": 1,
                        "created_at": "2025-05-10T21:45:00",
                        "updated_at": "2025-05-10T21:46:00",
                        "completed_at": "2025-05-10T21:46:00",
                        "execution_time": 60,
                        "result": {
                            "trends": [
                                {
                                    "topic": "AI in Healthcare",
                                    "score": 0.85,
                                    "sources": ["twitter", "reddit"],
                                    "sentiment": "positive",
                                }
                            ],
                            "analysis": "Healthcare AI is trending due to...",
                        },
                        "error": None,
                    }
                }
            },
        },
        403: {
            "description": "Not enough permissions",
            "content": {
                "application/json": {"example": {"detail": "Not enough permissions"}}
            },
        },
        404: {
            "description": "Task not found",
            "content": {"application/json": {"example": {"detail": "Task not found"}}},
        },
    },
)
async def read_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get task by ID."""
    task = db.query(AgentTask).filter(AgentTask.task_id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if task.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    # Get latest status from queue
    queue_status = queue_manager.get_task_status(task_id)
    if queue_status.get("status") != task.status:
        task.status = queue_status.get("status", task.status)
        if "result" in queue_status:
            task.result = queue_status["result"]
        if task.status in ["completed", "failed"]:
            task.completed_at = queue_status.get("updated_at")
        db.commit()
        db.refresh(task)

    return task


@router.get(
    "/tasks/",
    response_model=schemas.TaskList,
    summary="List tasks",
    description="""
    List all tasks with support for filtering and pagination.

    Parameters:
    - skip: Number of tasks to skip (for pagination)
    - limit: Maximum number of tasks to return
    - status: Filter by task status (pending, running, completed, failed)
    - agent_type: Filter by agent type (trend_analyzer, content_generator, scheduler)

    Note: Regular users can only see their own tasks.
    Superusers can see all tasks in the system.
    """,
    responses={
        200: {
            "description": "List of tasks",
            "content": {
                "application/json": {
                    "example": {
                        "tasks": [
                            {
                                "id": 1,
                                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                                "agent_type": "trend_analyzer",
                                "status": "completed",
                                "input_data": {
                                    "platforms": ["twitter", "reddit"],
                                    "categories": ["technology"],
                                    "time_range": "24h",
                                },
                                "user_id": 1,
                                "created_at": "2025-05-10T21:45:00",
                                "updated_at": "2025-05-10T21:46:00",
                                "completed_at": "2025-05-10T21:46:00",
                                "execution_time": 60,
                                "result": {
                                    "trends": [
                                        {
                                            "topic": "AI in Healthcare",
                                            "score": 0.85,
                                            "sources": ["twitter", "reddit"],
                                            "sentiment": "positive",
                                        }
                                    ],
                                    "analysis": "Healthcare AI is trending due to...",
                                },
                                "error": None,
                            }
                        ],
                        "total": 1,
                    }
                }
            },
        }
    },
)
async def list_tasks(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    agent_type: str | None = None,
    current_user: User = Depends(get_current_user),
) -> Any:
    """List tasks."""
    query = db.query(AgentTask)

    # Filter by user unless superuser
    if not current_user.is_superuser:
        query = query.filter(AgentTask.user_id == current_user.id)

    # Apply filters
    if status:
        query = query.filter(AgentTask.status == status)
    if agent_type:
        query = query.filter(AgentTask.agent_type == agent_type)

    total = query.count()
    tasks = query.order_by(AgentTask.created_at.desc()).offset(skip).limit(limit).all()

    # Update task statuses from queue
    for task in tasks:
        queue_status = queue_manager.get_task_status(task.task_id)
        if queue_status.get("status") != task.status:
            task.status = queue_status.get("status", task.status)
            if "result" in queue_status:
                task.result = queue_status["result"]
            if task.status in ["completed", "failed"]:
                task.completed_at = queue_status.get("updated_at")
    db.commit()
    db.refresh_all(tasks)

    return {"tasks": tasks, "total": total}


@router.delete(
    "/tasks/{task_id}",
    response_model=schemas.Message,
    summary="Delete task",
    description="""
    Delete a task by its UUID.

    Note: Regular users can only delete their own tasks.
    Superusers can delete any task.
    """,
    responses={
        200: {
            "description": "Task deleted successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Task deleted successfully"}
                }
            },
        },
        403: {
            "description": "Not enough permissions",
            "content": {
                "application/json": {"example": {"detail": "Not enough permissions"}}
            },
        },
        404: {
            "description": "Task not found",
            "content": {"application/json": {"example": {"detail": "Task not found"}}},
        },
    },
)
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Delete task by ID."""
    task = db.query(AgentTask).filter(AgentTask.task_id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if task.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}

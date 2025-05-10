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

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("", response_model=schemas.TaskInDB)
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
        user_id=current_user.id
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
            "user_id": current_user.id
        }
    )
    
    return db_task

@router.get("/{task_id}", response_model=schemas.TaskInDB)
async def read_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get task by ID."""
    task = db.query(AgentTask).filter(AgentTask.task_id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    if task.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
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

@router.get("", response_model=schemas.TaskList)
async def list_tasks(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    agent_type: str | None = None,
    current_user: User = Depends(get_current_user)
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

@router.delete("/{task_id}", response_model=schemas.Message)
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete task by ID."""
    task = db.query(AgentTask).filter(AgentTask.task_id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    if task.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
        
    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}

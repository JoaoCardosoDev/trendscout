from typing import Any
import json
import redis
from datetime import datetime

from .config import get_settings

settings = get_settings()


class QueueManager:
    """Manages task queues using Redis."""

    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True
        )

    def enqueue_task(self, queue_name: str, task_data: dict) -> str:
        """
        Add a task to the specified queue.
        Returns the task ID.
        """
        task_id = f"{queue_name}:{datetime.utcnow().timestamp()}"
        task_data["id"] = task_id
        task_data["status"] = "pending"
        task_data["created_at"] = datetime.utcnow().isoformat()

        # Add to queue
        self.redis_client.lpush(f"queue:{queue_name}", json.dumps(task_data))
        # Store task data
        self.redis_client.set(f"task:{task_id}", json.dumps(task_data))

        return task_id

    def get_task_status(self, task_id: str) -> dict:
        """Get the current status of a task."""
        task_data = self.redis_client.get(f"task:{task_id}")
        if task_data:
            return json.loads(task_data)
        return {"status": "not_found"}

    def update_task_status(self, task_id: str, status: str, result: Any = None) -> None:
        """Update the status and optionally the result of a task."""
        task_data = self.redis_client.get(f"task:{task_id}")
        if task_data:
            task_dict = json.loads(task_data)
            task_dict["status"] = status
            task_dict["updated_at"] = datetime.utcnow().isoformat()
            if result is not None:
                task_dict["result"] = result
            self.redis_client.set(f"task:{task_id}", json.dumps(task_dict))

    def get_next_task(self, queue_name: str) -> dict | None:
        """Get the next task from the specified queue."""
        task_data = self.redis_client.rpop(f"queue:{queue_name}")
        if task_data:
            return json.loads(task_data)
        return None


# Global queue manager instance
queue_manager = QueueManager()

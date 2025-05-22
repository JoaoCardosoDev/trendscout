from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB  # Add JSONB import
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import List, Dict, Any  # Add typing imports for the new field

from ..db.base_class import Base


class AgentTask(Base):
    """Model for tracking agent tasks and their results."""

    __tablename__ = "agent_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, index=True, nullable=False)
    agent_type = Column(
        String(50), nullable=False
    )  # trend_analyzer, content_generator, scheduler
    status = Column(String(20), nullable=False)  # pending, running, completed, failed
    input_data = Column(JSON)
    result = Column(JSON, nullable=True)
    error = Column(String(500), nullable=True)
    intermediate_steps = Column(JSONB, nullable=True)  # Add new field

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="tasks")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    execution_time = Column(Integer, nullable=True)  # in seconds

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..db.base_class import Base

class AgentTask(Base):
    """Model for tracking agent tasks and their results."""
    
    task_id = Column(String, unique=True, index=True, nullable=False)
    agent_type = Column(String, nullable=False)  # trend_analyzer, content_generator, scheduler
    status = Column(String, nullable=False)  # pending, running, completed, failed
    input_data = Column(JSON)
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", backref="tasks")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    execution_time = Column(Integer, nullable=True)  # in seconds

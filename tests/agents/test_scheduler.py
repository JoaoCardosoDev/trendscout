from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from crewai import Task

from trendscout.agents.scheduler import SchedulerAgent

@pytest.fixture
def scheduler():
    """Fixture that returns a SchedulerAgent instance."""
    return SchedulerAgent()

@pytest.fixture
def mock_ollama_service():
    """Fixture that returns a mock OllamaService."""
    return Mock()

def test_scheduler_config(scheduler):
    """Test scheduler agent configuration."""
    config = scheduler.get_agent_config()
    
    assert config["name"] == "Scheduler Agent"
    assert "role" in config
    assert "goal" in config
    assert "backstory" in config
    assert isinstance(config["role"], str)
    assert isinstance(config["goal"], str)
    assert isinstance(config["backstory"], str)

def test_get_optimal_time(scheduler, mock_ollama_service):
    """Test getting optimal publishing time."""
    mock_crew_agent = Mock()
    mock_crew_agent.execute_task.return_value = """
    {
        "schedule": {
            "recommended_time": "2025-05-15T14:30:00Z",
            "timezone": "UTC",
            "predicted_engagement": 0.85,
            "reasoning": "High user activity observed during this timeframe",
            "alternative_times": [
                "2025-05-15T18:30:00Z",
                "2025-05-16T09:30:00Z"
            ]
        }
    }
    """
    
    content_data = {
        "title": "The Future of AI",
        "target_audience": "Tech professionals",
        "content_type": "blog_post"
    }
    
    with patch("trendscout.agents.base.OllamaService", return_value=mock_ollama_service), \
         patch.object(scheduler, "create_crew_agent", return_value=mock_crew_agent):
        
        result = scheduler.get_optimal_time(content_data=content_data)
        
        # Verify the task was executed
        mock_crew_agent.execute_task.assert_called_once()
        
        # Verify the task content
        task: Task = mock_crew_agent.execute_task.call_args[0][0]
        assert isinstance(task, Task)
        assert content_data["title"] in task.description
        assert content_data["target_audience"] in task.description
        
        # Verify the result
        assert isinstance(result, dict)
        assert "schedule" in result
        assert "recommended_time" in result["schedule"]
        assert datetime.fromisoformat(result["schedule"]["recommended_time"].replace("Z", "+00:00"))

def test_get_optimal_time_with_platform(scheduler, mock_ollama_service):
    """Test getting optimal time for specific platform."""
    mock_crew_agent = Mock()
    mock_crew_agent.execute_task.return_value = "{}"
    
    content_data = {"title": "Test Content"}
    platform = "Twitter"
    
    with patch("trendscout.agents.base.OllamaService", return_value=mock_ollama_service), \
         patch.object(scheduler, "create_crew_agent", return_value=mock_crew_agent):
        
        scheduler.get_optimal_time(
            content_data=content_data,
            platform=platform
        )
        
        # Verify platform was included in task
        task: Task = mock_crew_agent.execute_task.call_args[0][0]
        assert platform in task.description

def test_get_optimal_time_with_timezone(scheduler, mock_ollama_service):
    """Test getting optimal time for specific timezone."""
    mock_crew_agent = Mock()
    mock_crew_agent.execute_task.return_value = "{}"
    
    content_data = {"title": "Test Content"}
    timezone = "Europe/London"
    
    with patch("trendscout.agents.base.OllamaService", return_value=mock_ollama_service), \
         patch.object(scheduler, "create_crew_agent", return_value=mock_crew_agent):
        
        scheduler.get_optimal_time(
            content_data=content_data,
            timezone=timezone
        )
        
        # Verify timezone was included in task
        task: Task = mock_crew_agent.execute_task.call_args[0][0]
        assert timezone in task.description

def test_get_optimal_time_invalid_response(scheduler, mock_ollama_service):
    """Test handling of invalid scheduling response."""
    mock_crew_agent = Mock()
    mock_crew_agent.execute_task.return_value = "Invalid JSON"
    
    content_data = {"title": "Test Content"}
    
    with patch("trendscout.agents.base.OllamaService", return_value=mock_ollama_service), \
         patch.object(scheduler, "create_crew_agent", return_value=mock_crew_agent):
        
        with pytest.raises(ValueError) as exc_info:
            scheduler.get_optimal_time(content_data=content_data)
        
        assert "Invalid scheduling response format" in str(exc_info.value)

def test_get_optimal_time_no_content_data(scheduler):
    """Test getting optimal time with no content data."""
    with pytest.raises(ValueError) as exc_info:
        scheduler.get_optimal_time(content_data={})
    
    assert "Content data must contain at least a title" in str(exc_info.value)

def test_get_optimal_time_invalid_platform(scheduler):
    """Test getting optimal time with invalid platform."""
    content_data = {"title": "Test Content"}
    
    with pytest.raises(ValueError) as exc_info:
        scheduler.get_optimal_time(
            content_data=content_data,
            platform="InvalidPlatform"
        )
    
    assert "Unsupported platform" in str(exc_info.value)

def test_get_optimal_time_invalid_timezone(scheduler):
    """Test getting optimal time with invalid timezone."""
    content_data = {"title": "Test Content"}
    
    with pytest.raises(ValueError) as exc_info:
        scheduler.get_optimal_time(
            content_data=content_data,
            timezone="Invalid/Timezone"
        )
    
    assert "Invalid timezone" in str(exc_info.value)

def test_get_optimal_time_custom_model(mock_ollama_service):
    """Test getting optimal time with custom model."""
    scheduler = SchedulerAgent(model_name="custom-model")
    mock_crew_agent = Mock()
    mock_crew_agent.execute_task.return_value = "{}"
    
    content_data = {"title": "Test Content"}
    
    with patch("trendscout.agents.base.OllamaService", return_value=mock_ollama_service), \
         patch.object(scheduler, "create_crew_agent", return_value=mock_crew_agent):
        
        scheduler.get_optimal_time(content_data=content_data)
        
        mock_ollama_service.get_llm.assert_called_once_with(model_name="custom-model")

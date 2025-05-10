from unittest.mock import Mock, patch

import pytest
from crewai import Task

from trendscout.agents.content_generator import ContentGeneratorAgent

@pytest.fixture
def content_generator():
    """Fixture that returns a ContentGeneratorAgent instance."""
    return ContentGeneratorAgent()

@pytest.fixture
def mock_ollama_service():
    """Fixture that returns a mock OllamaService."""
    return Mock()

def test_content_generator_config(content_generator):
    """Test content generator agent configuration."""
    config = content_generator.get_agent_config()
    
    assert config["name"] == "Content Generator Agent"
    assert "role" in config
    assert "goal" in config
    assert "backstory" in config
    assert isinstance(config["role"], str)
    assert isinstance(config["goal"], str)
    assert isinstance(config["backstory"], str)

def test_generate_content(content_generator, mock_ollama_service):
    """Test content generation execution."""
    mock_crew_agent = Mock()
    mock_crew_agent.execute_task.return_value = """
    {
        "content_ideas": [
            {
                "title": "The Future of AI Development",
                "description": "A deep dive into emerging AI trends",
                "target_audience": "Tech enthusiasts",
                "keywords": ["AI", "Machine Learning", "Future Tech"],
                "estimated_engagement": 0.85
            }
        ]
    }
    """
    
    trend_data = {
        "topic": "AI Development",
        "sentiment": "positive",
        "popularity": 0.85
    }
    
    with patch("trendscout.agents.base.OllamaService", return_value=mock_ollama_service), \
         patch.object(content_generator, "create_crew_agent", return_value=mock_crew_agent):
        
        result = content_generator.generate_content(trend_data=trend_data)
        
        # Verify the task was executed
        mock_crew_agent.execute_task.assert_called_once()
        
        # Verify the task content
        task: Task = mock_crew_agent.execute_task.call_args[0][0]
        assert isinstance(task, Task)
        assert "AI Development" in task.description
        
        # Verify the result
        assert isinstance(result, dict)
        assert "content_ideas" in result
        assert len(result["content_ideas"]) == 1
        assert "title" in result["content_ideas"][0]
        assert "description" in result["content_ideas"][0]

def test_generate_content_with_audience(content_generator, mock_ollama_service):
    """Test content generation with specific target audience."""
    mock_crew_agent = Mock()
    mock_crew_agent.execute_task.return_value = "{}"
    
    trend_data = {"topic": "AI Development"}
    target_audience = "Data Scientists"
    
    with patch("trendscout.agents.base.OllamaService", return_value=mock_ollama_service), \
         patch.object(content_generator, "create_crew_agent", return_value=mock_crew_agent):
        
        content_generator.generate_content(
            trend_data=trend_data,
            target_audience=target_audience
        )
        
        # Verify audience was included in task
        task: Task = mock_crew_agent.execute_task.call_args[0][0]
        assert target_audience in task.description

def test_generate_content_with_format(content_generator, mock_ollama_service):
    """Test content generation with specific content format."""
    mock_crew_agent = Mock()
    mock_crew_agent.execute_task.return_value = "{}"
    
    trend_data = {"topic": "AI Development"}
    content_format = "blog_post"
    
    with patch("trendscout.agents.base.OllamaService", return_value=mock_ollama_service), \
         patch.object(content_generator, "create_crew_agent", return_value=mock_crew_agent):
        
        content_generator.generate_content(
            trend_data=trend_data,
            content_format=content_format
        )
        
        # Verify format was included in task
        task: Task = mock_crew_agent.execute_task.call_args[0][0]
        assert content_format in task.description

def test_generate_content_invalid_response(content_generator, mock_ollama_service):
    """Test handling of invalid generation response."""
    mock_crew_agent = Mock()
    mock_crew_agent.execute_task.return_value = "Invalid JSON"
    
    trend_data = {"topic": "AI Development"}
    
    with patch("trendscout.agents.base.OllamaService", return_value=mock_ollama_service), \
         patch.object(content_generator, "create_crew_agent", return_value=mock_crew_agent):
        
        with pytest.raises(ValueError) as exc_info:
            content_generator.generate_content(trend_data=trend_data)
        
        assert "Invalid generation response format" in str(exc_info.value)

def test_generate_content_no_trend_data(content_generator):
    """Test content generation with no trend data."""
    with pytest.raises(ValueError) as exc_info:
        content_generator.generate_content(trend_data={})
    
    assert "Trend data must contain at least a topic" in str(exc_info.value)

def test_generate_content_invalid_format(content_generator):
    """Test content generation with invalid content format."""
    trend_data = {"topic": "AI Development"}
    
    with pytest.raises(ValueError) as exc_info:
        content_generator.generate_content(
            trend_data=trend_data,
            content_format="invalid_format"
        )
    
    assert "Unsupported content format" in str(exc_info.value)

def test_generate_content_custom_model(mock_ollama_service):
    """Test content generation with custom model."""
    generator = ContentGeneratorAgent(model_name="custom-model")
    mock_crew_agent = Mock()
    mock_crew_agent.execute_task.return_value = "{}"
    
    trend_data = {"topic": "AI Development"}
    
    with patch("trendscout.agents.base.OllamaService", return_value=mock_ollama_service), \
         patch.object(generator, "create_crew_agent", return_value=mock_crew_agent):
        
        generator.generate_content(trend_data=trend_data)
        
        mock_ollama_service.get_llm.assert_called_once_with(model_name="custom-model")

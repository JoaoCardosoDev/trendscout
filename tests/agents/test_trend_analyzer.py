from unittest.mock import Mock, patch

import pytest
from crewai import Task

from trendscout.agents.trend_analyzer import TrendAnalyzerAgent


@pytest.fixture
def trend_analyzer():
    """Fixture that returns a TrendAnalyzerAgent instance."""
    return TrendAnalyzerAgent()


@pytest.fixture
def mock_ollama_service():
    """Fixture that returns a mock OllamaService."""
    return Mock()


def test_trend_analyzer_config(trend_analyzer):
    """Test trend analyzer agent configuration."""
    config = trend_analyzer.get_agent_config()

    assert config["name"] == "Trend Analyzer Agent"
    assert "role" in config
    assert "goal" in config
    assert "backstory" in config
    assert isinstance(config["role"], str)
    assert isinstance(config["goal"], str)
    assert isinstance(config["backstory"], str)


def test_analyze_trends(trend_analyzer, mock_ollama_service):
    """Test trend analysis execution."""
    mock_crew_agent = Mock()
    mock_crew_agent.execute_task.return_value = """
    {
        "trends": [
            {
                "topic": "AI Development",
                "sentiment": "positive",
                "popularity": 0.85,
                "sources": ["Twitter", "Reddit"]
            }
        ]
    }
    """

    with patch(
        "trendscout.agents.base.OllamaService", return_value=mock_ollama_service
    ), patch.object(trend_analyzer, "create_crew_agent", return_value=mock_crew_agent):

        result = trend_analyzer.analyze_trends(platforms=["Twitter", "Reddit"])

        # Verify the task was executed
        mock_crew_agent.execute_task.assert_called_once()

        # Verify the task content
        task: Task = mock_crew_agent.execute_task.call_args[0][0]
        assert isinstance(task, Task)
        assert "Twitter" in task.description
        assert "Reddit" in task.description

        # Verify the result
        assert isinstance(result, dict)
        assert "trends" in result
        assert len(result["trends"]) == 1
        assert result["trends"][0]["topic"] == "AI Development"


def test_analyze_trends_with_custom_timeframe(trend_analyzer, mock_ollama_service):
    """Test trend analysis with custom timeframe."""
    mock_crew_agent = Mock()
    mock_crew_agent.execute_task.return_value = "{}"

    with patch(
        "trendscout.agents.base.OllamaService", return_value=mock_ollama_service
    ), patch.object(trend_analyzer, "create_crew_agent", return_value=mock_crew_agent):

        trend_analyzer.analyze_trends(platforms=["Twitter"], timeframe="last_week")

        # Verify timeframe was included in task
        task: Task = mock_crew_agent.execute_task.call_args[0][0]
        assert "last_week" in task.description.lower()


def test_analyze_trends_with_keywords(trend_analyzer, mock_ollama_service):
    """Test trend analysis with specific keywords."""
    mock_crew_agent = Mock()
    mock_crew_agent.execute_task.return_value = "{}"

    with patch(
        "trendscout.agents.base.OllamaService", return_value=mock_ollama_service
    ), patch.object(trend_analyzer, "create_crew_agent", return_value=mock_crew_agent):

        trend_analyzer.analyze_trends(
            platforms=["Twitter"], keywords=["AI", "Machine Learning"]
        )

        # Verify keywords were included in task
        task: Task = mock_crew_agent.execute_task.call_args[0][0]
        assert "AI" in task.description
        assert "Machine Learning" in task.description


def test_analyze_trends_invalid_response(trend_analyzer, mock_ollama_service):
    """Test handling of invalid analysis response."""
    mock_crew_agent = Mock()
    mock_crew_agent.execute_task.return_value = "Invalid JSON"

    with patch(
        "trendscout.agents.base.OllamaService", return_value=mock_ollama_service
    ), patch.object(trend_analyzer, "create_crew_agent", return_value=mock_crew_agent):

        with pytest.raises(ValueError) as exc_info:
            trend_analyzer.analyze_trends(platforms=["Twitter"])

        assert "Invalid analysis response format" in str(exc_info.value)


def test_analyze_trends_no_platforms(trend_analyzer):
    """Test trend analysis with no platforms specified."""
    with pytest.raises(ValueError) as exc_info:
        trend_analyzer.analyze_trends(platforms=[])

    assert "At least one platform must be specified" in str(exc_info.value)


def test_analyze_trends_invalid_platform(trend_analyzer):
    """Test trend analysis with invalid platform."""
    with pytest.raises(ValueError) as exc_info:
        trend_analyzer.analyze_trends(platforms=["InvalidPlatform"])

    assert "Unsupported platform" in str(exc_info.value)


def test_analyze_trends_custom_model(mock_ollama_service):
    """Test trend analysis with custom model."""
    analyzer = TrendAnalyzerAgent(model_name="custom-model")
    mock_crew_agent = Mock()
    mock_crew_agent.execute_task.return_value = "{}"

    with patch(
        "trendscout.agents.base.OllamaService", return_value=mock_ollama_service
    ), patch.object(analyzer, "create_crew_agent", return_value=mock_crew_agent):

        analyzer.analyze_trends(platforms=["Twitter"])

        mock_ollama_service.get_llm.assert_called_once_with(model_name="custom-model")

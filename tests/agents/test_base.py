from typing import Dict
from unittest.mock import Mock, patch

import pytest
from crewai import Agent, Task

from trendscout.agents.base import BaseAgent
from trendscout.core.ollama import OllamaService


class TestAgent(BaseAgent):
    """Test agent class that implements BaseAgent."""

    def get_agent_config(self) -> Dict:
        return {
            "name": "Test Agent",
            "role": "Test role",
            "goal": "Test goal",
            "backstory": "Test backstory",
        }


@pytest.fixture
def base_agent():
    """Fixture that returns a test agent instance."""
    return TestAgent()


@pytest.fixture
def mock_ollama_service():
    """Fixture that returns a mock OllamaService."""
    return Mock(spec=OllamaService)


def test_base_agent_creation(base_agent):
    """Test base agent creation with correct configuration."""
    assert isinstance(base_agent, BaseAgent)
    assert base_agent.get_agent_config()["name"] == "Test Agent"
    assert base_agent.get_agent_config()["role"] == "Test role"
    assert base_agent.get_agent_config()["goal"] == "Test goal"
    assert base_agent.get_agent_config()["backstory"] == "Test backstory"


def test_create_crew_agent(base_agent, mock_ollama_service):
    """Test creation of CrewAI agent."""
    with patch(
        "trendscout.agents.base.OllamaService", return_value=mock_ollama_service
    ):
        crew_agent = base_agent.create_crew_agent()

        assert isinstance(crew_agent, Agent)
        assert crew_agent.name == "Test Agent"
        assert crew_agent.role == "Test role"
        assert crew_agent.goal == "Test goal"
        assert crew_agent.backstory == "Test backstory"
        assert crew_agent.llm == mock_ollama_service.get_llm.return_value


def test_execute_task(base_agent, mock_ollama_service):
    """Test task execution."""
    mock_task = Mock(spec=Task)
    mock_task.description = "Test task description"
    mock_crew_agent = Mock()

    with patch(
        "trendscout.agents.base.OllamaService", return_value=mock_ollama_service
    ), patch.object(base_agent, "create_crew_agent", return_value=mock_crew_agent):

        base_agent.execute_task(mock_task)

        # Verify agent was created and task was executed
        base_agent.create_crew_agent.assert_called_once()
        mock_crew_agent.execute_task.assert_called_once_with(mock_task)


def test_execute_task_with_error(base_agent, mock_ollama_service):
    """Test task execution with error."""
    mock_task = Mock(spec=Task)
    mock_task.description = "Test task description"
    mock_crew_agent = Mock()
    mock_crew_agent.execute_task.side_effect = Exception("Test error")

    with patch(
        "trendscout.agents.base.OllamaService", return_value=mock_ollama_service
    ), patch.object(base_agent, "create_crew_agent", return_value=mock_crew_agent):

        with pytest.raises(Exception) as exc_info:
            base_agent.execute_task(mock_task)

        assert str(exc_info.value) == "Test error"
        base_agent.create_crew_agent.assert_called_once()
        mock_crew_agent.execute_task.assert_called_once_with(mock_task)


def test_agent_with_custom_model(mock_ollama_service):
    """Test agent creation with custom model."""
    custom_agent = TestAgent(model_name="custom-model")

    with patch(
        "trendscout.agents.base.OllamaService", return_value=mock_ollama_service
    ):
        crew_agent = custom_agent.create_crew_agent()

        mock_ollama_service.get_llm.assert_called_once_with(model_name="custom-model")
        assert crew_agent.llm == mock_ollama_service.get_llm.return_value


def test_agent_with_custom_temperature(mock_ollama_service):
    """Test agent creation with custom temperature."""
    custom_agent = TestAgent(temperature=0.8)

    with patch(
        "trendscout.agents.base.OllamaService", return_value=mock_ollama_service
    ):
        crew_agent = custom_agent.create_crew_agent()

        mock_ollama_service.get_llm.assert_called_once_with(
            model_name="llama2", temperature=0.8
        )
        assert crew_agent.llm == mock_ollama_service.get_llm.return_value


def test_agent_config_validation():
    """Test agent configuration validation."""

    class InvalidAgent(BaseAgent):
        def get_agent_config(self) -> Dict:
            return {
                "name": "Test Agent",
                # Missing required fields
            }

    with pytest.raises(ValueError) as exc_info:
        InvalidAgent()

    assert "Missing required fields in agent config" in str(exc_info.value)

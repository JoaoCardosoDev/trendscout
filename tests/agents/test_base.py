from unittest.mock import MagicMock, patch

import pytest
from crewai import Agent

from trendscout.agents.base import BaseAgent, ChatLiteLLM
from trendscout.core.config import get_settings

settings = get_settings()


# A concrete implementation of BaseAgent for testing purposes
class ConcreteTestAgent(BaseAgent):
    async def execute(self, *args, **kwargs):
        # Minimal implementation for testing
        return "execute_called"

    async def validate_result(self, result: any) -> bool:
        # Minimal implementation for testing
        return result == "execute_called"


@pytest.fixture
def test_agent_instance():
    return ConcreteTestAgent(
        name="Test Concrete Agent",
        role="Tester",
        goal="Test things",
        backstory="Born to test",
    )


@patch("trendscout.agents.base.ChatLiteLLM")
def test_base_agent_creation(mock_chat_litellm_class, test_agent_instance):
    """Test BaseAgent creation and property initialization."""
    # Use MagicMock with spec to make it behave more like a ChatLiteLLM instance
    mock_llm_instance = MagicMock(spec=ChatLiteLLM)
    # Ensure it has a 'callbacks' attribute, as crewAI might expect it
    mock_llm_instance.callbacks = []
    mock_chat_litellm_class.return_value = mock_llm_instance

    assert test_agent_instance.name == "Test Concrete Agent"
    assert test_agent_instance.role == "Tester"
    assert test_agent_instance.goal == "Test things"
    assert test_agent_instance.backstory == "Born to test"
    assert test_agent_instance.model == settings.OLLAMA_MODEL  # Default model
    assert test_agent_instance.temperature == 0.7  # Default temperature

    # Access the agent property to trigger its creation
    agent_prop = test_agent_instance.agent
    assert isinstance(agent_prop, Agent)
    mock_chat_litellm_class.assert_called_once_with(
        model=f"ollama/{settings.OLLAMA_MODEL}",
        temperature=0.7,
        request_timeout=settings.OLLAMA_REQUEST_TIMEOUT,
    )
    # The agent_prop.llm will be an instance of crewai.llm.LLM,
    # which wraps the mock_llm_instance.
    # We've already asserted that mock_chat_litellm_class was called with the correct params.
    # We can also check the type of the llm attribute of the crewAI agent.
    assert hasattr(agent_prop, "llm")
    # Further checks could involve inspecting agent_prop.llm if its internal structure was known
    # and stable, but for now, knowing it's an LLM wrapper and our mock was called is sufficient.


@patch("trendscout.agents.base.ChatLiteLLM")
def test_agent_with_custom_model(mock_chat_litellm_class):
    """Test BaseAgent with a custom model name."""
    custom_model = "custom_test_model"
    agent = ConcreteTestAgent(
        name="Custom Model Agent",
        role="Tester",
        goal="Test custom model",
        backstory="Uses a different model",
        model=custom_model,
    )
    mock_llm_instance = MagicMock(spec=ChatLiteLLM)
    mock_llm_instance.callbacks = []
    mock_chat_litellm_class.return_value = mock_llm_instance

    assert agent.model == custom_model
    # Access agent to trigger LLM instantiation
    _ = agent.agent
    mock_chat_litellm_class.assert_called_once_with(
        model=f"ollama/{custom_model}",
        temperature=0.7,  # Default temperature
        request_timeout=settings.OLLAMA_REQUEST_TIMEOUT,
    )


@patch("trendscout.agents.base.ChatLiteLLM")
def test_agent_with_custom_temperature(mock_chat_litellm_class):
    """Test BaseAgent with a custom temperature."""
    custom_temp = 0.9
    agent = ConcreteTestAgent(
        name="Custom Temp Agent",
        role="Tester",
        goal="Test custom temperature",
        backstory="Feeling warm",
        temperature=custom_temp,
    )
    mock_llm_instance = MagicMock(spec=ChatLiteLLM)
    mock_llm_instance.callbacks = []
    mock_chat_litellm_class.return_value = mock_llm_instance

    assert agent.temperature == custom_temp
    _ = agent.agent
    mock_chat_litellm_class.assert_called_once_with(
        model=f"ollama/{settings.OLLAMA_MODEL}",  # Default model
        temperature=custom_temp,
        request_timeout=settings.OLLAMA_REQUEST_TIMEOUT,
    )


# Removed test_execute_task as it was skipped due to async nature and not fitting the simplified test structure.
# Removed comments related to agent_config_validation and direct instantiation tests for brevity.


def test_base_agent_is_abstract():
    """Check that BaseAgent itself cannot be instantiated."""
    with pytest.raises(TypeError) as excinfo:
        BaseAgent(name="Abstract", role="r", goal="g", backstory="b")
    assert (
        "Can't instantiate abstract class BaseAgent with abstract methods execute, validate_result"
        in str(excinfo.value)
    )

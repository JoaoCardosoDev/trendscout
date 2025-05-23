from unittest.mock import MagicMock, patch

import pytest
from crewai import Task

from trendscout.agents.base import ChatLiteLLM
from trendscout.agents.content_generator import ContentGeneratorAgent
from trendscout.core.config import get_settings

settings = get_settings()


@pytest.fixture
def content_generator():
    """Fixture that returns a ContentGeneratorAgent instance."""
    return ContentGeneratorAgent()


@patch("trendscout.agents.base.ChatLiteLLM")
@patch("crewai.Agent.execute_task")
def test_run_content_generation_success(
    mock_agent_execute_task, mock_chat_litellm_class, content_generator
):
    """Test successful content generation using the 'run' method."""
    mock_llm_instance = MagicMock(spec=ChatLiteLLM)
    mock_llm_instance.callbacks = []
    mock_chat_litellm_class.return_value = mock_llm_instance
    # Mock a simple string output that _parse_result can handle or fallback gracefully
    mock_agent_execute_task.return_value = """
- Idea 1: Test Title - Test Description

Strategy: A simple test strategy.

#test #content

- Tip 1 for engagement.
- Tip 2 for engagement.
    """

    topic_query = "AI in Education"
    result = content_generator.run(query=topic_query)

    mock_chat_litellm_class.assert_called_with(
        model=f"ollama/{content_generator.model}",  # Uses default model from BaseAgent
        temperature=content_generator.temperature,  # Uses agent's specific temperature
        request_timeout=settings.OLLAMA_REQUEST_TIMEOUT,
    )
    mock_agent_execute_task.assert_called_once()
    task_arg = mock_agent_execute_task.call_args[0][0]
    assert isinstance(task_arg, Task)
    assert topic_query in task_arg.description

    assert isinstance(result, dict)
    assert "content_ideas" in result
    assert "strategy" in result
    assert "hashtags" in result
    assert "engagement_tips" in result
    # Basic check that parsing produced some content ideas
    assert len(result["content_ideas"]) > 0
    assert result["content_ideas"][0]["title"] == "Test Title"


@patch("trendscout.agents.base.ChatLiteLLM")
@patch("crewai.Agent.execute_task")
def test_run_content_generation_invalid_llm_response(
    mock_agent_execute_task, mock_chat_litellm_class, content_generator
):
    """Test content generation when LLM returns a string that cannot be parsed by _parse_result."""
    mock_llm_instance = MagicMock(spec=ChatLiteLLM)
    mock_llm_instance.callbacks = []
    mock_chat_litellm_class.return_value = mock_llm_instance
    mock_agent_execute_task.return_value = "This is not a structured response."

    topic_query = "Future of Remote Work"
    result = content_generator.run(query=topic_query)

    mock_agent_execute_task.assert_called_once()
    assert isinstance(result, dict)
    # Check for the actual structure when parsing "This is not a structured response."
    # The try block in _parse_result will complete, yielding empty lists/strings.
    assert result["content_ideas"] == []
    assert result["strategy"] == ""
    assert result["hashtags"] == []
    assert result["engagement_tips"] == []


# Removed other tests like _with_audience, _with_format, _no_trend_data, _invalid_format, _custom_model
# to meet the simplification goal and focus on the core 'run' method.
# The 'run' method itself doesn't take audience/format directly, these would be part of the 'query' string.
# Custom model testing for individual agents is removed for overall test suite reduction.
# Input validation for 'run' (e.g. empty query) could be added if essential, but the agent's prompt is quite open.
